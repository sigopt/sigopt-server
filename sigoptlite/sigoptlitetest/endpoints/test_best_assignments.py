# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import numpy
import pytest

from sigoptlite.best_assignments import BestAssignmentsLogger
from sigoptlite.builders import LocalExperimentBuilder
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_PARAMETERS


class TestBestAssignmentsLogger(UnitTestsBase):
  @staticmethod
  def assert_observation_lists_are_equal(list_1, list_2):
    assert len(list_1) == len(list_2) and all(l1 in list_2 for l1 in list_1)

  @staticmethod
  def assert_observations_are_sorted(observations, experiment):
    default_metric = experiment.metrics[0] if experiment.is_search else experiment.optimized_metrics[0]
    metric_values = []
    for observation in observations:
      metric_values.append(next(meval for meval in observation.values if meval.name == default_metric.name).value)

    if default_metric.objective == "minimize":
      assert sorted(metric_values) == metric_values
    else:
      assert sorted(metric_values, reverse=True) == metric_values

  def create_observations_with_values_in_simplex(self, experiment, on_boundary=False, num=10):
    y1_values = numpy.linspace(0, 1, num=num)
    observations = []

    for y1 in y1_values:  # Create observations according to simplex in lower right quadrant
      y2 = y1 - 1
      best_observation_assignments = self.make_random_suggestions(experiment)[0].assignments
      alpha = 1 if on_boundary else numpy.random.uniform(low=0, high=0.8)

      best_observation_values = [
        dict(name="y1", value=alpha * y1),
        dict(name="y2", value=alpha * y2),
      ]
      best_observation = self.make_observation(
        experiment=experiment,
        assignments=best_observation_assignments,
        values=best_observation_values,
      )
      observations.append(best_observation)
    return observations

  @pytest.mark.parametrize(
    "feature",
    [
      "default",
      "multimetric",
      "metric_constraint",
      "metric_threshold",
      "search",
    ],
  )
  def test_failed_observations(self, feature):
    # No observations
    experiment_meta = self.get_experiment_feature(feature)
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = []
    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert best_observations_from_logger == []

    # All observations are failures
    for _ in range(10):
      observation = self.make_observation(
        experiment=experiment,
        assignments=self.make_random_suggestions(experiment)[0].assignments,
        failed=True,
      )
      observations.append(observation)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert best_observations_from_logger == []

  @pytest.mark.parametrize("objective, best_value", [("maximize", 100), ("minimize", -100)])
  def test_single_metric(self, objective, best_value):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"][0]["objective"] = objective
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = self.make_random_observations(experiment, num_observations=10)

    best_observation_assignments = self.make_random_suggestions(experiment)[0].assignments
    best_observation_values = [dict(name="y1", value=best_value)]
    best_observation = self.make_observation(
      experiment=experiment,
      assignments=best_observation_assignments,
      values=best_observation_values,
    )
    observations.append(best_observation)
    random.shuffle(observations)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == 1
    assert best_observation == best_observations_from_logger[0]

  def test_multimetric(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment = LocalExperimentBuilder(experiment_meta)
    pareto_optimal_observations = self.create_observations_with_values_in_simplex(experiment, on_boundary=True)
    non_optimal_observations = self.create_observations_with_values_in_simplex(experiment, on_boundary=False)
    observations = pareto_optimal_observations + non_optimal_observations
    random.shuffle(observations)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    self.assert_observations_are_sorted(best_observations_from_logger, experiment)
    self.assert_observation_lists_are_equal(best_observations_from_logger, pareto_optimal_observations)

  @pytest.mark.parametrize("threshold_y1, threshold_y2", [(None, -0.25), (0.25, None), (0.25, -0.25)])
  def test_multimetric_thresholds(self, threshold_y1, threshold_y2):
    experiment_meta = dict(
      parameters=DEFAULT_PARAMETERS,
      metrics=[
        dict(name="y1", objective="maximize", threshold=threshold_y1),
        dict(name="y2", objective="minimize", threshold=threshold_y2),
      ],
      observation_budget=123,
    )
    experiment = LocalExperimentBuilder(experiment_meta)
    pareto_optimal_observations = self.create_observations_with_values_in_simplex(experiment, on_boundary=True)
    non_optimal_observations = self.create_observations_with_values_in_simplex(experiment, on_boundary=False)
    observations = pareto_optimal_observations + non_optimal_observations
    random.shuffle(observations)

    if threshold_y1 is None:
      threshold_y1 = 0

    if threshold_y2 is None:
      threshold_y2 = 0

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    self.assert_observations_are_sorted(best_observations_from_logger, experiment)

    for observation in pareto_optimal_observations:
      if observation.values[0].value >= threshold_y1 and observation.values[1].value <= threshold_y2:
        assert observation in best_observations_from_logger
      else:
        assert observation not in best_observations_from_logger

  def test_metric_constraints(self):
    experiment_meta = self.get_experiment_feature("metric_constraint")
    assert experiment_meta["metrics"][0]["strategy"] == "constraint"
    threshold = experiment_meta["metrics"][0]["threshold"]
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = self.make_random_observations(experiment, num_observations=25)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == 1

    best_observation = best_observations_from_logger[0]
    assert best_observation.values[0].value >= threshold

    valid_observations = best_assignments_logger.filter_valid_full_cost_observations(observations)
    for observation in valid_observations:
      assert best_observation.values[1].value <= observation.values[1].value

  def test_multimetric_search(self):
    experiment_meta = self.get_experiment_feature("search")
    thresholds = [m["threshold"] for m in experiment_meta["metrics"]]
    objectives = [m["objective"] for m in experiment_meta["metrics"]]
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = self.make_random_observations(experiment, num_observations=25)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    self.assert_observations_are_sorted(best_observations_from_logger, experiment)

    for best_observation in best_observations_from_logger:
      for i, metric in enumerate(best_observation.values):
        if objectives[i] == "maximize":
          assert metric.value >= thresholds[i]
        if objectives[i] == "minimize":
          assert metric.value <= thresholds[i]

    valid_observations = best_assignments_logger.filter_valid_full_cost_observations(observations)
    assert len(best_observations_from_logger) > 1
    self.assert_observation_lists_are_equal(best_observations_from_logger, valid_observations)

  def test_multitask(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = []
    for _ in range(20):
      observation_with_task = self.make_observation(
        experiment=experiment,
        assignments=self.make_random_suggestions(experiment)[0].assignments,
        values=[dict(name="y1", value=numpy.random.rand())],
        task=numpy.random.choice(experiment_meta["tasks"]),
      )
      observations.append(observation_with_task)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == 1
    assert best_observations_from_logger[0].task.cost == 1
    assert best_observations_from_logger[0].task.name == "expensive"

  def test_multisolutions(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    num_solutions = experiment_meta["num_solutions"]
    experiment = LocalExperimentBuilder(experiment_meta)
    best_assignments_logger = BestAssignmentsLogger(experiment)
    observations = []
    for _ in range(num_solutions):
      observation = self.make_observation(
        experiment=experiment,
        assignments=self.make_random_suggestions(experiment)[0].assignments,
        values=[dict(name="y1", value=numpy.random.rand())],
      )
      observations.append(observation)
      best_observations_from_logger = best_assignments_logger.fetch(observations)
      self.assert_observation_lists_are_equal(best_observations_from_logger, observations)

    observations.extend(self.make_random_observations(experiment, 100))
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == num_solutions
