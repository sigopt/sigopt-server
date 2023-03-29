# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from flaky import flaky
from sklearn import datasets

from libsigopt.aux.importances import compute_importances
from testaux.numerical_test_case import NumericalTestCase


class TestImportancesComputation(NumericalTestCase):
  @pytest.mark.parametrize("n_samples", [50, 200, 800])
  @pytest.mark.parametrize("n_features", [3, 10, 60])
  def test_basic_functionalities(self, n_samples, n_features):
    # pylint: disable=unbalanced-tuple-unpacking
    features, values = datasets.make_regression(
      n_samples=n_samples,
      n_features=n_features,
      noise=0.2,
    )
    importances = compute_importances(features, values)
    assert len(importances) == n_features
    self.assert_scalar_within_relative(sum(importances), 1, 1e-9)

  @flaky(max_runs=2)
  def test_actually_compute_importances(self):
    features, values, coef = datasets.make_regression(
      n_samples=50,
      n_features=3,
      n_informative=2,
      noise=0.2,
      coef=True,
    )
    importances = compute_importances(features, values)
    assert len(importances) == 3
    self.assert_scalar_within_relative(sum(importances), 1, 1e-9)
    large_importances = importances[coef != 0]
    small_importance = importances[coef == 0][0]
    assert numpy.all(large_importances > small_importance)

  @pytest.mark.parametrize("n_features", [3, 10, 60])
  def test_constant_observation_values(self, n_features):
    # pylint: disable=unbalanced-tuple-unpacking
    features, values = datasets.make_regression(
      n_samples=200,
      n_features=n_features,
      noise=0.2,
    )
    values = numpy.zeros(200)
    importances = compute_importances(features, values)
    assert len(importances) == n_features
    self.assert_scalar_within_relative(sum(importances), 1, 1e-9)
    self.assert_vector_within_relative(importances, numpy.full_like(importances, 1 / n_features), 1e-9)
