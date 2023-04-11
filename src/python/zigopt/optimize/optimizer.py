# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.common import *
from zigopt.assignments.model import extract_array_for_computation_from_assignments
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.observation.model import Observation
from zigopt.optimize.args import OptimizationArgs
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.optimize.sources.conditional import ConditionalOptimizationSource
from zigopt.optimize.sources.search import SearchOptimizationSource
from zigopt.optimize.sources.spe import SPEOptimizationSource
from zigopt.redis.service import RedisServiceTimeoutError
from zigopt.services.base import Service

from libsigopt.aux.geometry_utils import compute_distance_matrix_squared


class OptimizerService(Service):
  def trigger_next_points(self, experiment):
    optimization_args = self.fetch_optimization_args(experiment)

    suggestions = optimization_args.source.get_suggestions(optimization_args)

    # Check all observations, all open suggestions, and all unprocessed suggestions for duplicates
    if not (experiment.conditionals or experiment.tasks) and self.services.config_broker.get(
      "features.severeDuplicateCheck", False
    ):
      optimization_args_for_dedupe = self.fetch_optimization_args(experiment)
      self.services.logging_service.getLogger("sigopt.optimize.dedupe").info(
        "Before dedupe: %s",
        [s.id for s in suggestions],
      )
      suggestions = self.exclude_duplicate_suggestions(
        optimization_args_for_dedupe,
        suggestions,
        experiment,
      )
      self.services.logging_service.getLogger("sigopt.optimize.dedupe").info(
        "After dedupe: %s",
        [s.id for s in suggestions],
      )

    self.persist_suggestions(experiment, suggestions)

    return optimization_args.max_observation_id

  def trigger_hyperparameter_optimization(self, experiment):
    optimization_args = self.fetch_optimization_args(experiment)
    source = optimization_args.source

    current_aux_date_updated = current_datetime()
    new_hyperparameters = source.get_hyperparameters(optimization_args)

    self.services.aux_service.persist_hyperparameters(
      experiment,
      source.name,
      new_hyperparameters,
      current_aux_date_updated,
    )
    return optimization_args.max_observation_id

  def fetch_observation_iter(self, experiment):
    counts = self.services.observation_service.get_observation_counts(experiment.id)

    query = (
      self.services.database_service.query(Observation)
      .filter(Observation.experiment_id == experiment.id)
      .filter(Observation.id <= counts.max_observation_id)
      .filter(~Observation.data.deleted.as_boolean())
    )

    observation_iter = self.services.database_service.stream(500, query.limit(counts.observation_count))

    return observation_iter, counts

  def fetch_optimization_args(self, experiment):
    observation_iter, counts = self.fetch_observation_iter(experiment)
    observation_count = counts.observation_count
    failure_count = counts.failure_count
    max_observation_id = counts.max_observation_id

    source = self.get_inferred_optimization_source(
      experiment,
      observation_count,
    )
    old_hyperparameters = self.services.aux_service.get_stored_hyperparameters(
      experiment,
      source,
    )

    open_suggestions = self.services.suggestion_service.find_open_by_experiment(experiment)
    last_observation = self.services.observation_service.last_observation(experiment)

    return OptimizationArgs(
      source=source,
      observation_iterator=observation_iter,
      observation_count=observation_count,
      failure_count=failure_count,
      max_observation_id=max_observation_id,
      old_hyperparameters=old_hyperparameters,
      open_suggestions=open_suggestions,
      last_observation=last_observation,
    )

  def ensure_not_deleted(self, experiment):
    return self.services.experiment_service.find_by_id(experiment.id)

  def persist_suggestions(self, experiment, suggestions, timestamp=None):
    if suggestions:
      experiment = self.ensure_not_deleted(experiment)
      if experiment:
        try:
          self.services.unprocessed_suggestion_service.insert_unprocessed_suggestions(suggestions, timestamp)
        except RedisServiceTimeoutError as e:
          self.services.exception_logger.log_exception(
            e,
            extra={
              "function_name": "insert_unprocessed_suggestions",
              "experiment_id": experiment.id,
            },
          )

  def should_use_spe(self, experiment, num_observations):
    if self.services.config_broker.get("model.force_spe", False):
      return True
    if experiment.conditionals:
      return False
    return not CategoricalOptimizationSource(self.services, experiment).is_suitable_at_this_point(num_observations)

  def get_inferred_optimization_source(
    self,
    experiment,
    num_observations,
  ):
    if experiment.conditionals:
      return ConditionalOptimizationSource(self.services, experiment)
    if self.should_use_spe(experiment, num_observations):
      return SPEOptimizationSource(self.services, experiment)
    if experiment.is_search or experiment.num_solutions > 1:
      return SearchOptimizationSource(self.services, experiment)
    return CategoricalOptimizationSource(self.services, experiment)

  def exclude_duplicate_suggestions(self, optimization_args, suggestions, experiment):
    tol = 0
    if not suggestions:
      return []

    parameters = [p.copy_protobuf() for p in experiment.all_parameters]

    suggestion_matrix = numpy.empty((len(suggestions), len(parameters)))
    for row, s in enumerate(suggestions):
      extract_array_for_computation_from_assignments(
        s.suggestion_meta.suggestion_data,
        parameters,
        vals=suggestion_matrix[row, :],
      )

    self.services.logging_service.getLogger("sigopt.optimize.dedupe").debug("suggestion_matrix: %s", suggestion_matrix)

    acceptable_logical_array_by_observations = numpy.full(len(suggestions), True, dtype=bool)
    acceptable_logical_array_by_open = numpy.full(len(suggestions), True, dtype=bool)

    if optimization_args.observation_count:
      observation_matrix = numpy.empty((optimization_args.observation_count, len(parameters)))
      for row, o in enumerate(optimization_args.observation_iterator):
        extract_array_for_computation_from_assignments(o.data, parameters, vals=observation_matrix[row, :])

      suggestion_observation_distance = compute_distance_matrix_squared(observation_matrix, suggestion_matrix)
      min_distance_each_suggestion = numpy.min(suggestion_observation_distance, axis=0)
      acceptable_logical_array_by_observations = min_distance_each_suggestion > tol

    if optimization_args.open_suggestions:
      open_matrix = numpy.empty((len(optimization_args.open_suggestions), len(parameters)))
      for row, os in enumerate(optimization_args.open_suggestions):
        extract_array_for_computation_from_assignments(
          os.suggestion_meta.suggestion_data,
          parameters,
          vals=open_matrix[row, :],
        )

      suggestion_open_distance = compute_distance_matrix_squared(open_matrix, suggestion_matrix)
      min_distance_each_suggestion = numpy.min(suggestion_open_distance, axis=0)
      acceptable_logical_array_by_open = min_distance_each_suggestion > tol

    suggestion_is_acceptable = numpy.logical_and(
      acceptable_logical_array_by_observations,
      acceptable_logical_array_by_open,
    )
    self.services.logging_service.getLogger("sigopt.optimize.dedupe").debug(
      "suggestion_is_acceptable: %s",
      suggestion_is_acceptable,
    )
    return [s for k, s in enumerate(suggestions) if suggestion_is_acceptable[k]]
