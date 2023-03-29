# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import numpy
import pytest

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME
from libsigopt.compute.covariance import C2RadialMatern, SquareExponential
from libsigopt.compute.domain import CategoricalDomain, FixedIndicesOnContinuousDomain
from libsigopt.compute.expected_improvement import AugmentedExpectedImprovement, ExpectedImprovement
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.multitask_acquisition_function import MultitaskAcquisitionFunction
from libsigopt.compute.multitask_covariance import MultitaskTensorCovariance
from libsigopt.compute.vectorized_optimizers import AdamOptimizer, DEOptimizer
from testaux.numerical_test_case import NumericalTestCase
from testcompute.vectorized_optimizers_test import QuadraticFunction


class TestVectorizedOptimizersWithFixedParameters(NumericalTestCase):
  def test_basic_optimization(self):
    cat_domain = CategoricalDomain([{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 2]}] * 5)
    fixed_indices = {0: 1, 3: -1}
    domain = FixedIndicesOnContinuousDomain(cat_domain.one_hot_domain, fixed_indices)

    true_sol = numpy.zeros(5)
    af = QuadraticFunction(domain, true_sol)
    optimizer = DEOptimizer(acquisition_function=af, domain=domain, num_multistarts=30, maxiter=100)
    best_solution, _ = optimizer.optimize(numpy.atleast_2d(true_sol))

    fixed_sol_full = numpy.array([1, 0, 0, -1, 0])
    self.assert_vector_within_relative(best_solution, fixed_sol_full, 1e-7)

  def test_constrained_optimization(self):
    cat_domain = CategoricalDomain(
      domain_components=[{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 2]}] * 5,
      constraint_list=[
        {
          "rhs": 1,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
          "weights": [0, 1, 1, 0, 1],
        },
      ],
    )

    fixed_indices = {0: 1, 3: -1}
    domain = FixedIndicesOnContinuousDomain(cat_domain.one_hot_domain, fixed_indices)

    true_sol = numpy.ones(5) * 0.5
    af = QuadraticFunction(domain, true_sol)
    optimizer = DEOptimizer(acquisition_function=af, domain=domain, num_multistarts=30, maxiter=100)
    best_solution, _ = optimizer.optimize(numpy.atleast_2d(true_sol))

    fixed_sol_full = numpy.array([1, 0.5, 0.5, -1, 0.5])
    self.assert_vector_within_relative(best_solution, fixed_sol_full, 1e-7)


class TestAcquisitionFunctionWithFixedParameters(NumericalTestCase):
  @classmethod
  @pytest.fixture(autouse=True, scope="class")
  def base_setup(cls):
    return cls._base_setup()

  @classmethod
  def _base_setup(cls):
    cls.domain = CategoricalDomain(
      [
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 1.0]},
      ]
    ).one_hot_domain

    list_hyps = [1.0, 0.3, 0.3, 0.4]
    cls.cov = SquareExponential(list_hyps)
    cls.mtcov = MultitaskTensorCovariance(list_hyps, C2RadialMatern, SquareExponential)

    x = cls.domain.generate_quasi_random_points_in_domain(14)
    y = numpy.sum(x**2, axis=1)
    v = numpy.full_like(y, 1e-3)
    cls.data = HistoricalData(cls.domain.dim)
    cls.data.append_historical_data(x, y, v)

    cls.mpi = [[0] * cls.domain.dim]
    cls.gp = GaussianProcess(cls.cov, cls.data, cls.mpi)

  @pytest.mark.parametrize("acquisition_function", [ExpectedImprovement, AugmentedExpectedImprovement])
  @pytest.mark.parametrize("optimizer_class", [DEOptimizer, AdamOptimizer])
  def test_fixed_parameter_af_evaluation(self, acquisition_function, optimizer_class):
    fixed_values = self.domain.generate_quasi_random_points_in_domain(1)[0]
    fixed_indices = {self.domain.dim - 1: fixed_values[-1]}
    domain = FixedIndicesOnContinuousDomain(self.domain, fixed_indices)
    mtaf = MultitaskAcquisitionFunction(acquisition_function(GaussianProcess(self.mtcov, self.data, self.mpi)))
    opt = optimizer_class(
      acquisition_function=mtaf,
      domain=domain,
      num_multistarts=50,
      maxiter=100,
    )
    best_location, _ = opt.optimize()
    assert self.domain.check_point_acceptable(best_location)
    assert best_location[-1] == fixed_values[-1]
