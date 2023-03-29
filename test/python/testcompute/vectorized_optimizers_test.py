# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import namedtuple

import numpy
import pytest

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME
from libsigopt.compute.acquisition_function import AcquisitionFunction
from libsigopt.compute.covariance import SquareExponential
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.expected_improvement import ExpectedParallelImprovement
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.vectorized_optimizers import AdamOptimizer, DEOptimizer
from libsigopt.compute.views.rest.gp_next_points_categorical import form_augmented_domain
from testaux.numerical_test_case import NumericalTestCase


class QuadraticFunction(AcquisitionFunction):
  def __init__(self, domain, maxima_point):
    num_points = 5
    dim = domain.dim
    hd = HistoricalData(dim)
    hd.append_historical_data(
      points_sampled=numpy.ones((num_points, dim)),
      points_sampled_value=numpy.ones(num_points),
      points_sampled_noise_variance=numpy.ones(num_points),
    )
    cov = SquareExponential([0.1] * (dim + 1))
    fake_gp = GaussianProcess(cov, hd)
    super().__init__(fake_gp)
    self._maxima_point = numpy.copy(maxima_point)

  @property
  def optimum_point(self):
    return self._maxima_point

  @property
  def optimum_value(self):
    return 0.0

  def _evaluate_at_point_list(self, points_to_evaluate):
    return -numpy.sum((points_to_evaluate - self._maxima_point) ** 2, axis=1)

  def _evaluate_grad_at_point_list(self, points_to_evaluate):
    return -2.0 * (points_to_evaluate - self._maxima_point)


class TestOptimizer(NumericalTestCase):
  @classmethod
  @pytest.fixture(autouse=True, scope="class")
  def base_setup(cls):
    return cls._base_setup()

  @classmethod
  def _base_setup(cls):
    """Set up a test case for optimizing a simple quadratic polynomial."""
    cls.dim = 3
    domain_components = [{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-0.5, 0.5]}]
    cat_domain = CategoricalDomain(domain_components * cls.dim)
    cls.domain = cat_domain.one_hot_domain

    maxima_point = numpy.full(cls.dim, 0.0)
    cls.af = QuadraticFunction(cls.domain, maxima_point)

  @pytest.mark.parametrize("optimizer_class", [AdamOptimizer, DEOptimizer])
  def test_optimizer_base(self, optimizer_class):
    # Check that optimizers generate the right number of points
    optimizer = optimizer_class(
      acquisition_function=self.af,
      domain=self.domain,
      num_multistarts=5,
      maxiter=0,
    )
    _, all_results = optimizer.optimize(numpy.atleast_2d([0] * self.dim))
    assert len(all_results.ending_points) == len(all_results.starting_points) == 5

    # Check that optimizers automatically restrict points to within the domain
    optimizer = optimizer_class(
      acquisition_function=self.af,
      domain=self.domain,
      num_multistarts=5,
      maxiter=1,
    )
    best_location, all_results = optimizer.optimize(numpy.atleast_2d([2] * self.dim))
    for pt in all_results.ending_points:
      assert self.domain.check_point_acceptable(pt)
    assert self.domain.check_point_acceptable(best_location)

    # Verify that the optimizer does not move from the optima if we start it there.
    optimum_point = self.af.optimum_point
    optimizer = optimizer_class(
      acquisition_function=self.af,
      domain=self.domain,
      num_multistarts=10,
      maxiter=1,
    )
    best_result, _ = optimizer.optimize(numpy.atleast_2d(optimum_point))
    self.assert_vector_within_relative(best_result, optimum_point, 2.0 * numpy.finfo(numpy.float64).eps)

    # Start near the optimal, should get closer
    optimizer = optimizer_class(
      acquisition_function=self.af,
      domain=self.domain,
      num_multistarts=50,
    )
    epsilon = 0.01
    best_result, _ = optimizer.optimize(numpy.atleast_2d(optimum_point + epsilon))

    # Verify coordinates are closer to the optimum than starting location
    self.assert_vector_within_relative(best_result, optimum_point, epsilon)

    # Verify function value improved over starting values
    starter_value = self.af.evaluate_at_point_list(numpy.atleast_2d(optimum_point + epsilon))
    value = self.af.evaluate_at_point_list(numpy.atleast_2d(best_result))
    assert value >= starter_value

  @pytest.mark.parametrize("optimizer_class", [DEOptimizer, AdamOptimizer])
  def test_optimizer_invalid_parameter_type(self, optimizer_class):
    parameter_type = namedtuple("Parameter_type", ["invalid_p"])
    with pytest.raises(TypeError):
      optimizer_class(
        acquisition_function=self.af,
        domain=self.domain,
        num_multistarts=5,
        maxiter=0,
        optimizer_parameters=parameter_type,
      )

  @pytest.mark.parametrize("optimizer_class", [DEOptimizer, AdamOptimizer])
  def test_domain_with_constraints(self, optimizer_class):
    dim = 5
    coeff_vector = [1, 1, 1, 1, 1]
    rhs = 0.0

    domain = CategoricalDomain(
      domain_components=[{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 1]}] * dim,
      constraint_list=[
        {"weights": coeff_vector, "rhs": rhs, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )

    af = QuadraticFunction(domain.one_hot_domain, numpy.full(dim, 0.0))
    optimizer = optimizer_class(
      acquisition_function=af,
      domain=domain.one_hot_domain,
      num_multistarts=20,
      maxiter=100,
    )
    best_result, _ = optimizer.optimize()

    assert domain.one_hot_domain.check_point_satisfies_constraints(best_result)
    assert not domain.one_hot_domain.check_point_on_boundary(best_result)
    assert domain.check_point_acceptable(best_result)

  def test_qei_vectorized(self):
    dim = 3
    N = 5
    num_to_sample = 3

    domain = CategoricalDomain([{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 1]}] * dim)
    x = domain.generate_quasi_random_points_in_domain(N)
    y = 6 - numpy.log(1 + numpy.sum(x**2, axis=1))
    data = HistoricalData(dim)
    data.append_historical_data(x, y, numpy.full_like(y, 1e-3))
    cov = SquareExponential([1.0] + [(N / 2) ** (-1 / dim)] * dim)
    gp = GaussianProcess(cov, data, [[0] * dim])
    epi = ExpectedParallelImprovement(gp, num_to_sample)
    qei_domain = form_augmented_domain(domain, epi)
    de = DEOptimizer(qei_domain.one_hot_domain, epi, 10, maxiter=10)
    results = de.optimize()
    assert len(results[0]) == dim * num_to_sample
