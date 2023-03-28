# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.aux.constant import MULTISOLUTION_TOP_OBSERVATIONS_FRACTION
from libsigopt.aux.multimetric import find_pareto_frontier_observations_for_maximization

from sigoptlite.sources import BaseOptimizationSource


class BestAssignmentsLogger(object):
  def __init__(self, experiment):
    self.experiment = experiment
    self.full_task_cost = None
    if self.experiment.is_multitask:
      self.full_task_cost = max([task.cost for task in self.experiment.tasks])

  def observation_is_valid_and_full_cost(self, observation):
    if observation.failed:
      return False
    if self.experiment.is_multitask and observation.task.cost != self.full_task_cost:
      return False
    return observation.within_metric_thresholds(self.experiment)

  def filter_valid_full_cost_observations(self, observations):
    return [o for o in observations if self.observation_is_valid_and_full_cost(o)]

  def get_default_metric_for_experiment(self):
    return self.experiment.constraint_metrics[0] if self.experiment.is_search else self.experiment.optimized_metrics[0]

  def single_metric_best_from_observations(self, observations):
    valid_observations = self.filter_valid_full_cost_observations(observations)
    if not valid_observations:
      return []
    default_metric = self.get_default_metric_for_experiment()
    best_observation = max(valid_observations, key=lambda o: o.get_value_for_maximization(default_metric))
    return [best_observation]

  def pareto_frontier_from_observations(self, observations):
    valid_observations = self.filter_valid_full_cost_observations(observations)
    if not valid_observations:
      return []

    optimized_values_for_maximization = [
      o.get_optimized_measurements_for_maximization(self.experiment) for o in valid_observations
    ]
    pareto_frontier_observations, _ = find_pareto_frontier_observations_for_maximization(
      optimized_values_for_maximization, valid_observations
    )
    return pareto_frontier_observations

  def multisolutions_best_from_observations(self, observations):
    valid_observations = self.filter_valid_full_cost_observations(observations)
    if not valid_observations:
      return []

    default_metric = self.get_default_metric_for_experiment()
    valid_observations.sort(key=lambda o: o.get_value_for_maximization(default_metric))
    top_observation_last_index = max(
      round(len(valid_observations) * MULTISOLUTION_TOP_OBSERVATIONS_FRACTION),
      self.experiment.num_solutions,
    )
    top_observations = valid_observations[:top_observation_last_index]
    if len(top_observations) <= self.experiment.num_solutions:
      return top_observations

    best_indices = BaseOptimizationSource.multisolution_best_assignments(
      experiment=self.experiment,
      observations=top_observations,
    )
    best_indices.sort()
    return [top_observations[i] for i in best_indices]

  def fetch(self, observations):
    if self.experiment.is_search:
      best_observations = self.filter_valid_full_cost_observations(observations)
    elif self.experiment.requires_pareto_frontier_optimization:
      best_observations = self.pareto_frontier_from_observations(observations)
    elif self.experiment.is_multisolution:
      best_observations = self.multisolutions_best_from_observations(observations)
    else:
      best_observations = self.single_metric_best_from_observations(observations)

    default_metric = self.get_default_metric_for_experiment()
    best_observations.sort(key=lambda o: o.get_value_for_maximization(default_metric), reverse=True)
    return [b.get_client_observation(self.experiment) for b in best_observations]
