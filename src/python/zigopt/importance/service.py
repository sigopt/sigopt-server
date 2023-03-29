# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.common import *
from zigopt.services.base import Service

from libsigopt.aux.importances import compute_importances


class ImportancesService(Service):
  @staticmethod
  def minimum_valid_observations_to_compute_importances(experiment):
    return 5 * len(experiment.all_parameters)

  @staticmethod
  def can_update_importances(experiment, num_observations):
    return (
      len(experiment.all_parameters) > 1
      and not experiment.development
      and not experiment.conditionals
      and num_observations >= ImportancesService.minimum_valid_observations_to_compute_importances(experiment)
    )

  def should_update_importances(self, experiment, observation_count):
    # Want to make sure we show importances as soon as they are available.
    # Also want to make sure that when the experiment is over, the customer
    # gets the "final" importances.

    start_of_window = ImportancesService.minimum_valid_observations_to_compute_importances(experiment)
    end_of_window = experiment.observation_budget or 0

    if observation_count > self.services.config_broker.get("features.importancesMaxObservations", 5000):
      return False

    if observation_count < start_of_window:
      return False

    if observation_count == start_of_window:
      return True

    if observation_count == end_of_window:
      return True

    # Make sure importances are queued when there is a bulk observation create (ie CSV uploads)
    if observation_count > start_of_window and not experiment.experiment_meta.importance_maps:
      return True

    # As the experiment progresses, decrease the probability of updating
    # As written, the probability of each observation triggering an update is 20%
    # at 200 points, 10% at 400 points, 5% at 800 points, 2.5% at 1600 points, etc.
    probability_of_update = 0.2
    scaling_factor = 200
    return non_crypto_random.random() < probability_of_update * min([1, (scaling_factor / observation_count)])

  def compute_parameter_importances(self, experiment):
    valid_observations = self.services.observation_service.find_valid_observations(experiment)
    if not self.can_update_importances(experiment, len(valid_observations)):
      return None

    features = [
      [
        o.get_assignment(p) if not p.has_log_transformation else numpy.log10(o.get_assignment(p))
        for p in experiment.all_parameters
      ]
      for o in valid_observations
    ]

    # metric values for each observation sorted by metric name
    metric_values_per_obs = [o.data.sorted_all_metric_values(experiment) for o in valid_observations]

    importance_maps = {}
    # Iterate through the metrics and calculate importances separately for each one
    # NOTE: this expects that metric_importances/detail is also using all_metrics
    for i, m in enumerate(experiment.all_metrics):

      metric_values = [values[i] for values in metric_values_per_obs]
      feature_importances = compute_importances(features, metric_values)
      feature_importances_map = {p.name: fi for p, fi in zip(experiment.all_parameters, feature_importances)}
      importance_maps[m.name] = feature_importances_map

    self.persist_importances(experiment, importance_maps)

    return max_option([o.id for o in valid_observations])

  def persist_importances(self, experiment, importance_maps):
    self.services.experiment_service.update_importance_maps(experiment, importance_maps)
