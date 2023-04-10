# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import case, desc, func

from zigopt.common import *
from zigopt.json.builder import ObservationProgressJsonBuilder, RunProgressJsonBuilder
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMetric
from zigopt.services.base import Service
from zigopt.training_run.model import TrainingRun


class BaseExperimentProgress:
  builder_cls: object

  def __init__(self, experiment):
    self.experiment = experiment

  @property
  def experiment_id(self):
    return self.experiment.id

  def json_builder(self):
    return self.builder_cls(self.experiment, self)


class ExperimentRunProgress(BaseExperimentProgress):
  builder_cls = RunProgressJsonBuilder

  def __init__(self, experiment, finished_run_count, active_run_count):
    super().__init__(experiment)
    self.finished_run_count = finished_run_count
    self.active_run_count = active_run_count


class ExperimentObservationProgress(BaseExperimentProgress):
  builder_cls = ObservationProgressJsonBuilder

  def __init__(self, experiment, status_quo, best_observation, last_observation, count, observation_budget_consumed):
    super().__init__(experiment)
    self.status_quo = status_quo
    self.best_observation = best_observation
    self.last_observation = last_observation
    self.count = count
    self.observation_budget_consumed = observation_budget_consumed


class ExperimentProgressService(Service):
  def empty_progress(self, experiment):
    if experiment.runs_only:
      return ExperimentRunProgress(experiment, 0, 0)
    return ExperimentObservationProgress(experiment, None, None, None, 0, 0)

  def progress_for_experiments(self, experiments, should_fetch_best=True):
    progress_map = {e.id: self.empty_progress(e) for e in experiments}
    runs_experiments, observations_experiments = partition(experiments, lambda e: e.runs_only)
    self._run_progress_for_experiments(runs_experiments, progress_map)
    self._observation_progress_for_experiments(observations_experiments, should_fetch_best, progress_map)
    return progress_map

  def _run_progress_for_experiments(self, experiments, progress_map):
    experiment_map = {e.id: e for e in experiments}

    for eid, finished_count, active_count in self.services.database_service.all(
      self.services.database_service.query(
        TrainingRun.experiment_id,
        func.count(case([(TrainingRun.completed.isnot(None), 1)])),
        func.count(case([(TrainingRun.completed.is_(None), 1)])),
      )
      .filter(TrainingRun.experiment_id.in_([e.id for e in experiments]))
      .filter(~TrainingRun.deleted)
      .group_by(TrainingRun.experiment_id)
    ):
      experiment = experiment_map[eid]
      progress_map[eid] = ExperimentRunProgress(
        experiment=experiment,
        finished_run_count=finished_count,
        active_run_count=active_count,
      )

  def _observation_progress_for_experiments(self, experiments, should_fetch_best, progress_map):
    last_observations = {}
    first_observations = {}
    observation_counts = {}
    budget_sums = {}

    for eid, last, first, count, budget_sum in self.services.database_service.all(
      self.services.database_service.query(
        Observation.experiment_id,
        func.max(Observation.id),
        func.min(Observation.id),
        func.count(Observation.id),
        func.sum(Observation.data.task.cost.as_numeric()),
      )
      .filter(Observation.experiment_id.in_([e.id for e in experiments]))
      .filter(~Observation.data.deleted.as_boolean())
      .group_by(Observation.experiment_id)
    ):
      last_observations[eid] = last
      first_observations[eid] = first
      observation_counts[eid] = count
      budget_sums[eid] = budget_sum

    best_observations = {}
    if should_fetch_best:
      experiments_eligible_for_best = [e for e in experiments if len(e.optimized_metrics) == 1]
      if experiments_eligible_for_best:
        experiments_by_optimized_index = as_grouped_dict(
          experiments_eligible_for_best,
          lambda e: find_index(e.all_metrics, lambda m: m.strategy == ExperimentMetric.OPTIMIZE),
        )

        num_indexes = len(experiments_by_optimized_index)
        if num_indexes > 2:
          self.services.logging_service.getLogger("sigopt.progress").warning(
            "Found %s optimized indexes for progress call with experiments %s",
            num_indexes,
            [e.id for e in experiments_eligible_for_best],
          )
        for optimized_metric_index, exp_list in experiments_by_optimized_index.items():

          # Tricky query using window functions to compute max value
          # https://www.postgresql.org/docs/9.5/static/tutorial-window.html
          # http://docs.sqlalchemy.org/en/latest/core/tutorial.html#window-functions
          # TODO(SN-1079): This query can be pretty expensive when lots of experiments
          # have lots of observations (~100ms). I don't see any immediate optimizations so
          # it may be worth considering denormalizing the best observation somewhere, or
          # reconsidering our need for this query in prod
          min_exps, max_exps = partition(experiments_eligible_for_best, lambda e: e.optimized_metrics[0].is_minimized)
          value_clause = Observation.data.values[optimized_metric_index].value.as_numeric()

          for v_clause, exp_list in [(desc(value_clause), max_exps), (value_clause, min_exps)]:
            if exp_list:
              subquery = (
                self.services.database_service.query(
                  Observation.experiment_id.label("experiment_id"),
                  Observation.id.label("observation_id"),
                  func.rank().over(partition_by=Observation.experiment_id, order_by=v_clause).label("rank"),
                )
                .filter(Observation.experiment_id.in_([e.id for e in exp_list]))
                .filter(~Observation.data.deleted.as_boolean())
                .filter(~Observation.data.reported_failure.as_boolean())
                .filter(Observation.data.task.cost.as_numeric() == 1)
                .subquery("q")
              )
              for eid, best, _ in self.services.database_service.all(
                self.services.database_service.query(subquery).filter(subquery.c.rank == 1)
              ):
                best_observations[eid] = best

    observations = self.services.observation_service.find_by_ids(
      distinct(
        flatten(
          [
            last_observations.values(),
            first_observations.values(),
            best_observations.values(),
          ]
        )
      )
    )
    observations_map = to_map_by_key(observations, lambda o: o.id)

    progress_map.update(
      (
        e.id,
        ExperimentObservationProgress(
          experiment=e,
          status_quo=observations_map.get(first_observations.get(e.id)),
          best_observation=observations_map.get(best_observations.get(e.id)),
          last_observation=observations_map.get(last_observations.get(e.id)),
          count=observation_counts.get(e.id, 0),
          observation_budget_consumed=budget_sums.get(e.id, 0),
        ),
      )
      for e in experiments
    )
