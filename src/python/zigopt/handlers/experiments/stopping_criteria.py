# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from libsigopt.aux.multimetric import find_pareto_frontier_observations_for_maximization

from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import StoppingCriteriaJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


# If there has been no change after 5D observations, start reporting possible stagnation
LOOKBACK_FACTOR = 5

# The number of best results to consider for measuring stagnation, rather than just the top result
NUM_TOP_RESULTS_TO_CHECK = 5

# TODO(RTL-104): Be more intelligent regarding how multisolution is handled when it exists
class ExperimentsStoppingCriteriaHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def get_values_for_maximization_with_features_replaced(self):
    observations = self.services.observation_service.all_data(self.experiment)
    replacement_values = [-numpy.inf] * len(self.experiment.optimized_metrics)

    # Replace failed observations with values that cannot be the best found/on the frontier
    values = []
    for o in reversed(observations):
      values.append(
        replacement_values
        if o.reported_failure
        else [o.value_for_maximization(self.experiment, m.name) for m in self.experiment.optimized_metrics]
      )

    return numpy.array(values), len(observations)

  def handle(self):
    reported_values, num_observations = self.get_values_for_maximization_with_features_replaced()
    lookback_depth = LOOKBACK_FACTOR * self.experiment.dimension

    observation_budget_reached = False
    if self.experiment.observation_budget:
      observation_budget_reached = num_observations > self.experiment.observation_budget

    possible_stagnation = False
    if reported_values.shape[0] > lookback_depth + NUM_TOP_RESULTS_TO_CHECK - 1:
      # TODO(RTL-105): Make the multiple optimized metric computation more efficient
      if self.experiment.requires_pareto_frontier_optimization or self.experiment.num_solutions > 1:
        if observation_budget_reached:
          old_values = reported_values[:-lookback_depth]
          old_indices, _ = find_pareto_frontier_observations_for_maximization(old_values, range(len(old_values)))
          old_frontier = {tuple(old_values[index]) for index in old_indices}
          current_indices, _ = find_pareto_frontier_observations_for_maximization(
            reported_values, range(len(reported_values))
          )
          current_frontier = {tuple(reported_values[index]) for index in current_indices}
          possible_stagnation = old_frontier == current_frontier
      elif self.experiment.is_search:
        # TODO(RTL-106): consider a proper stopping criteria for search. It's not trivial to compute one
        # without calling into compute.
        possible_stagnation = False
      else:
        lookback_points_in_order = sorted(reported_values[:-lookback_depth, 0])
        top_threshold_looking_back = lookback_points_in_order[-NUM_TOP_RESULTS_TO_CHECK]
        best_value_since_lookback = max(reported_values[-lookback_depth:, 0])
        possible_stagnation = top_threshold_looking_back >= best_value_since_lookback

    return StoppingCriteriaJsonBuilder.json(
      possible_stagnation=possible_stagnation,
      observation_budget_reached=observation_budget_reached,
    )
