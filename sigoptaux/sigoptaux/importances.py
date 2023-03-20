# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from sklearn.ensemble import ExtraTreesRegressor


def _get_n_estimators(n_dimensions, n_observations):
  if n_dimensions <= 50 and n_observations <= 10000:
    n_estimators = 100
  else:
    n_estimators = 50
  return n_estimators


def compute_importances(features, values):
  assert len(features) == len(values)
  features = numpy.asarray(features)
  n_observations, n_dimensions = features.shape
  assert len(features.shape) == 2
  n_estimators = _get_n_estimators(len(features[0]), len(features))
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
