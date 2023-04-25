# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import is_number, max_option, remove_nones_sequence
from zigopt.experiment.util import get_experiment_default_metric_name
from zigopt.services.base import Service

from libsigopt.aux.constant import MULTISOLUTION_TOP_OBSERVATIONS_FRACTION
from libsigopt.aux.errors import SigoptComputeError
from libsigopt.aux.multimetric import find_pareto_frontier_observations_for_maximization


class ExperimentBestObservationService(Service):
  """Finds the best points available for an experiment."""

  # NOTE: None can be used here because in the single metric case the observations are unused
  def best_from_valid_observations(self, experiment, observations):
    default_metric_name = get_experiment_default_metric_name(experiment)
    return max_option(observations, key=lambda o: o.value_for_maximization(experiment, default_metric_name))

  def pareto_frontier(self, experiment, observations):
    valid_observations = self.services.observation_service.valid_observations(observations)
    if not valid_observations:
      return []
    optimized_values_for_maximization = [
      [m.value for m in o.get_optimized_measurements_for_maximization(experiment)] for o in valid_observations
    ]
    pareto_frontier_observations, _ = find_pareto_frontier_observations_for_maximization(
      optimized_values_for_maximization, valid_observations
    )
    return pareto_frontier_observations

  def multiple_solutions_best(self, experiment, observations):
    best_observations = self.multi_metric_best(experiment, observations, pareto_frontier=False)
    top_observation_last_index = max(
      round(len(observations) * MULTISOLUTION_TOP_OBSERVATIONS_FRACTION),
      experiment.num_solutions,
    )
    top_observations = best_observations[:top_observation_last_index]
    if len(top_observations) <= experiment.num_solutions:
      return top_observations

    try:
      best_indices = self.services.sc_adapter.multisolution_best_assignments(
        experiment=experiment,
        observations=top_observations,
      )
    except SigoptComputeError as e:
      # fallback to return the best observations if SigoptComputeError
      num_solutions = experiment.num_solutions
      self.services.exception_logger.soft_exception(
        f"multisolution_best_assignments failed. Returning best {num_solutions} observations",
        extra=dict(
          error_message=e,
        ),
      )
      return best_observations[:num_solutions]

    best_indices.sort()  # always returns the best values in order
    return [top_observations[i] for i in best_indices]

  def single_metric_best(self, experiment, observations, cost=None):
    valid_observations = self.services.observation_service.valid_observations(observations, cost)
    valid_observations = [o for o in valid_observations if o.within_metric_thresholds(experiment)]
    return self.best_from_valid_observations(experiment, valid_observations)

  def multi_metric_best(self, experiment, observations, pareto_frontier):
    default_metric_name = get_experiment_default_metric_name(experiment)
    best_observations = [o for o in observations if o.within_metric_thresholds(experiment)]
    if pareto_frontier:
      best_observations = self.pareto_frontier(experiment, best_observations)
    best_observations = [
      o for o in best_observations if is_number(o.value_for_maximization(experiment, default_metric_name))
    ]
    best_observations.sort(key=lambda o: o.value_for_maximization(experiment, default_metric_name), reverse=True)
    return best_observations

  def get_best_observations(self, experiment, observations):
    if experiment.requires_pareto_frontier_optimization:
      best_observations = self.multi_metric_best(experiment, observations, pareto_frontier=True)
    elif experiment.is_search:
      best_observations = self.multi_metric_best(experiment, observations, pareto_frontier=False)
    elif experiment.num_solutions > 1:
      best_observations = self.multiple_solutions_best(experiment, observations)
    else:
      best_observation = self.single_metric_best(experiment, observations, cost=1)
      best_observations = remove_nones_sequence([best_observation])
    return best_observations
