# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from scipy.spatial.distance import cdist

from libsigopt.aux.geometry_utils import compute_distance_matrix_squared
from testaux.numerical_test_case import NumericalTestCase


class TestDistanceMatrix(NumericalTestCase):
  @pytest.mark.parametrize("dim", [5, 10, 15])
  @pytest.mark.parametrize("num_x", [10, 100, 1000])
  @pytest.mark.parametrize("num_z", [100, 200, 300])
  def test_distance_is_correct(self, dim, num_x, num_z):
    x = numpy.random.random((num_x, dim))
    z = numpy.random.random((num_z, dim))
    dm_sq = compute_distance_matrix_squared(x, z)
    dm_sq_cdist = cdist(x, z) ** 2
    self.assert_vector_within_relative_norm(dm_sq, dm_sq_cdist, tol=1e-15 * dim, norm=numpy.inf)
