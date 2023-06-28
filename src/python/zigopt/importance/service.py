# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Sequence

import numpy
from sklearn.ensemble import ExtraTreesRegressor

from zigopt.common import *
from zigopt.experiment.model import Experiment
from zigopt.services.base import Service


def compute_importances(features: Sequence[Sequence[float]], values: Sequence[float]) -> numpy.ndarray:
  def _get_n_estimators(n_dimensions, n_observations):
    if n_dimensions <= 50 and n_observations <= 10000:
      n_estimators = 100
    else:
      n_estimators = 50
    return n_estimators

  assert len(features) == len(values)
  np_features = numpy.asarray(features)
  n_observations, n_dimensions = np_features.shape
  assert len(np_features.shape) == 2
  n_estimators = _get_n_estimators(*np_features.shape)
  values_max, values_min = max(values), min(values)

  # NOTE: Normalize the values before feeding them to the random forest model,
  # and output equal importances if the metric values are approaching a constant value
  if numpy.isclose(values_max, values_min):
    return numpy.ones(n_dimensions) / n_dimensions

  values_normalized = (numpy.asarray(values) - values_min) / (values_max - values_min)
  # NOTE: We are not one-hot encoding categorical parameters. Oh well.
  n_estimators = _get_n_estimators(n_dimensions, n_observations)
  clf = ExtraTreesRegressor(n_estimators=n_estimators, random_state=0)
  feature_importances = clf.fit(features, values_normalized).feature_importances_

  if (not numpy.all(numpy.isfinite(feature_importances))) or numpy.all(feature_importances == 0):
    return numpy.ones(n_dimensions) / n_dimensions

  return feature_importances


class ImportancesService(Service):
  @staticmethod
  def minimum_valid_observations_to_compute_importances(experiment: Experiment) -> int:
    return 5 * len(experiment.all_parameters)

  @staticmethod
  def can_update_importances(experiment: Experiment, num_observations: int) -> bool:
    return (
      len(experiment.all_parameters) > 1
      and not experiment.development
      and not experiment.conditionals
      and num_observations >= ImportancesService.minimum_valid_observations_to_compute_importances(experiment)
    )

  def should_update_importances(self, experiment: Experiment, observation_count: int) -> bool:
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

  def compute_parameter_importances(self, experiment: Experiment) -> int | None:
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

  def persist_importances(self, experiment: Experiment, importance_maps: dict[str, dict[str, float]]) -> None:
    self.services.experiment_service.update_importance_maps(experiment, importance_maps)
