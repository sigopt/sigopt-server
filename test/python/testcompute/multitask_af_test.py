# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import numpy
import pytest
from flaky import flaky

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME
from libsigopt.compute.covariance import SquareExponential
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.expected_improvement import (
  AugmentedExpectedImprovement,
  ExpectedImprovement,
  ExpectedImprovementWithFailures,
  ExpectedParallelImprovement,
)
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.multitask_acquisition_function import MultitaskAcquisitionFunction
from libsigopt.compute.probabilistic_failures import ProbabilisticFailuresCDF
from testaux.numerical_test_case import NumericalTestCase


class TestMultitaskAcquisitionFunction(NumericalTestCase):
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
    cls.cov = SquareExponential([1.0, 0.3, 0.3, 0.4])

    x = cls.domain.generate_quasi_random_points_in_domain(14)
    y = numpy.random.random(len(x))
    v = numpy.full_like(y, 1e-1)
    cls.data = HistoricalData(3)
    cls.data.append_historical_data(x, y, v)
    points_being_sampled = cls.domain.generate_quasi_random_points_in_domain(2)

    cls.gp = GaussianProcess(cls.cov, cls.data, [[0, 0, 0]])
    threshold = numpy.random.uniform(0.2, 0.6)
    pf = ProbabilisticFailuresCDF(cls.gp, threshold)

    cls.ei = ExpectedImprovement(cls.gp)
    cls.eif = ExpectedImprovementWithFailures(cls.gp, pf)
    cls.aei = AugmentedExpectedImprovement(cls.gp)
    cls.qei = ExpectedParallelImprovement(cls.gp, 1, points_being_sampled=points_being_sampled)

  def test_creation(self):
    for af in (self.ei, self.eif, self.aei, self.qei):
      multitask_af = MultitaskAcquisitionFunction(af)
      new_point = self.domain.generate_quasi_random_points_in_domain(1)

      af_val = multitask_af.evaluate_at_point_list(new_point)[0]
      assert not (numpy.isnan(af_val) or numpy.isinf(af_val))

      if multitask_af.differentiable:
        af_grad = multitask_af.evaluate_grad_at_point_list(new_point)[0]
        assert af_grad.shape == (multitask_af.dim,)
        assert not numpy.any(numpy.isnan(af_grad)) or numpy.any(numpy.isinf(af_grad))

  # In this test we give the same function values at the same locations for all the costs
  # Then we confirm that the MTEI prefers lower costs if the predictions are the same for all tasks
  def test_lower_cost_preferred(self):
    task_options = [0.1, 0.3, 1.0]

    x = numpy.tile(self.data.points_sampled[:, :-1], (len(task_options), 1))
    task_costs = numpy.tile(task_options, (len(self.data.points_sampled), 1)).T.reshape(-1, 1)
    x = numpy.concatenate((x, task_costs), axis=1)
    y = numpy.tile(self.data.points_sampled_value, (len(task_options),))
    v = numpy.full_like(y, 1e-2)
    data = HistoricalData(self.data.dim)
    data.append_historical_data(x, y, v)

    gp = GaussianProcess(self.cov, data, [[0] * data.dim])
    ei = ExpectedImprovement(gp)
    multitask_ei = MultitaskAcquisitionFunction(ei)

    new_points_with_costs = self.domain.generate_quasi_random_points_in_domain(5)
    new_points = numpy.tile(new_points_with_costs[:, :-1], (len(task_options), 1))
    task_costs = numpy.tile(task_options, (len(new_points_with_costs), 1)).T.reshape(-1, 1)
    new_points = numpy.concatenate((new_points, task_costs), axis=1)
    mtei_vals = multitask_ei.evaluate_at_point_list(new_points)
    ei_vals = ei.evaluate_at_point_list(new_points)
    ei_vals_points_per_task = numpy.reshape(ei_vals, (3, 5)).T
    largest_ei_diff = numpy.max(abs(numpy.diff(ei_vals_points_per_task, axis=1)))
    mtei_vals_points_per_task = numpy.reshape(mtei_vals, (3, 5)).T
    assert numpy.allclose(ei_vals_points_per_task / task_options, mtei_vals_points_per_task)
    # MTEI prefers lower costs up to the largest difference of ei * task
    upper_bound_on_mtei_diff = largest_ei_diff * numpy.min(numpy.diff(task_options))
    assert numpy.all(numpy.diff(mtei_vals_points_per_task, axis=1) < upper_bound_on_mtei_diff)

  # NOTE: This test implicitly tests the joint_function_gradient_eval in all the other AFs
  @flaky(max_runs=3)
  def test_joint_function_gradient_eval(self):
    test_points = self.domain.generate_quasi_random_points_in_domain(4)
    for af in (self.ei, self.eif, self.aei, self.qei):
      multitask_af = MultitaskAcquisitionFunction(af)
      if multitask_af.differentiable:
        vals, grad_vals = multitask_af.joint_function_gradient_eval(test_points)
        for test_point, val, grad_val in zip(test_points, vals, grad_vals):
          val_compare = multitask_af.evaluate_at_point_list(numpy.atleast_2d(test_point))[0]
          grad_val_compare = multitask_af.evaluate_grad_at_point_list(numpy.atleast_2d(test_point))[0]
          self.assert_scalar_within_relative(val, val_compare, 1e-13)
          self.assert_vector_within_relative(grad_val, grad_val_compare, 1e-12)
      else:
        with pytest.raises(NotImplementedError):
          multitask_af.joint_function_gradient_eval(test_points)
        vals = multitask_af.evaluate_at_point_list(test_points)
        # This test incorporates the stochastic nature of AF that have no gradient
        for test_point, val in zip(test_points, vals):
          val_compare_list = [multitask_af.evaluate_at_point_list(numpy.atleast_2d(test_point))[0] for _ in range(50)]
          assert abs(val - numpy.mean(val_compare_list)) < 3 * numpy.std(val_compare_list)
