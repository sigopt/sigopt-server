# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from flaky import flaky

from libsigopt.compute.covariance import SquareExponential
from libsigopt.compute.domain import ContinuousDomain
from libsigopt.compute.expected_improvement import (
  ExpectedImprovement,
  ExpectedImprovementWithFailures,
  ExpectedParallelImprovement,
)
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.vectorized_optimizers import AdamOptimizer
from testcompute.gaussian_process_test_case import GaussianProcessTestCase


class TestExpectedImprovement(GaussianProcessTestCase):
  """Verify that the "naive" and "vectorized" EI implementations in Python return the same result.
    The code for the naive implementation of EI is straightforward to read whereas the vectorized version is a lot more
    opaque. So we verify one against the other.
    Fully verifying the monte carlo implementation (e.g., conducting convergence tests, comparing against analytic
    results) is expensive and already a part of the C++ unit test suite.
    """

  @classmethod
  def _check_ei_symmetry(cls, ei_eval, point_to_sample, shifts):
    """Compute ei at each ``[point_to_sample +/- shift for shift in shifts]`` and check for equality."""
    for shift in shifts:
      left_ei = ei_eval.evaluate_at_point_list(numpy.atleast_2d(point_to_sample - shift))[0]
      left_grad_ei = ei_eval.evaluate_grad_at_point_list(numpy.atleast_2d(point_to_sample - shift))[0]

      right_ei = ei_eval.evaluate_at_point_list(numpy.atleast_2d(point_to_sample + shift))[0]
      right_grad_ei = ei_eval.evaluate_grad_at_point_list(numpy.atleast_2d(point_to_sample + shift))[0]

      cls.assert_scalar_within_relative(left_ei, right_ei, 5.0e-15)
      cls.assert_vector_within_relative(left_grad_ei, -right_grad_ei, 5.0e-15)

  def test_1d_analytic_ei_edge_cases(self):
    """Test cases where analytic EI would attempt to compute 0/0 without variance lower bounds."""
    base_coord = numpy.array([[0.5]])
    points = numpy.array([base_coord, base_coord * 2.0])
    values = numpy.array([-1.809342, -1.09342])
    value_vars = numpy.array([0, 0])

    # First a symmetric case: only one historical point
    data = HistoricalData(1)
    data.append_historical_data(points[0], values[0, None], value_vars[0, None])

    hyperparameters = numpy.array([0.2, 0.3])
    covariance = SquareExponential(hyperparameters)
    gaussian_process = GaussianProcess(covariance, data)

    ei_eval = ExpectedImprovement(gaussian_process)

    ei = ei_eval.evaluate_at_point_list(base_coord)[0]
    grad_ei = ei_eval.evaluate_grad_at_point_list(base_coord)[0]
    self.assert_scalar_within_relative(ei, 0.0, 1.0e-14)
    self.assert_vector_within_relative(grad_ei, numpy.zeros(grad_ei.shape), 1.0e-15)

    shifts = (2.0e-15, 4.0e-11, 3.14e-6, 8.89e-1, 2.71)
    self._check_ei_symmetry(ei_eval, base_coord[0], shifts)

    # Now introduce some asymmetry with a second point
    # Right side has a larger objetive value, so the EI minimum
    # is shifted *slightly* to the left of best_value.
    data.append_historical_data(points[1], values[1, None], value_vars[1, None])
    gaussian_process = GaussianProcess(covariance, data)
    shift = 3.0e-12
    ei_eval = ExpectedImprovement(gaussian_process)
    ei = ei_eval.evaluate_at_point_list(base_coord - shift)[0]
    grad_ei = ei_eval.evaluate_grad_at_point_list(base_coord - shift)[0]
    self.assert_scalar_within_relative(ei, 0.0, 1.0e-14)
    self.assert_vector_within_relative(grad_ei, numpy.zeros(grad_ei.shape), 1.0e-15)

  def test_best_value_and_location(self, gaussian_process_list):
    for gaussian_process in gaussian_process_list:
      ei = ExpectedImprovement(gaussian_process)
      self.assert_scalar_within_relative(ei.best_value, gaussian_process.best_observed_value, 1.0e-14)
      self.assert_vector_within_relative(ei.best_location, gaussian_process.best_observed_location, 1.0e-14)

  def test_evaluate_ei_at_points_for_base_ei(self, one_hot_domain_list, gaussian_process_list):
    domain, gaussian_process = one_hot_domain_list[-1], gaussian_process_list[-1]

    ei_eval = ExpectedImprovement(gaussian_process)

    num_to_eval = 10
    points_to_evaluate = domain.generate_quasi_random_points_in_domain(num_to_eval)

    test_values = ei_eval.evaluate_at_point_list(points_to_evaluate)

    # NOTE: Because of the vectorization in distance matrix computation these can be off near unit roundoff
    for i, value in enumerate(test_values):
      truth = ei_eval.evaluate_at_point_list(points_to_evaluate[i, None, :])[0]
      self.assert_scalar_within_relative(value, truth, 1.0e-8)

  def test_qei_working(self, one_hot_domain_list, gaussian_process_list):
    for domain, gaussian_process in zip(one_hot_domain_list, gaussian_process_list):
      all_points = domain.generate_quasi_random_points_in_domain(9)

      for i in range(2, len(all_points)):
        points_to_sample = all_points[:i]
        ei_eval = ExpectedParallelImprovement(
          gaussian_process,
          len(points_to_sample),
          num_mc_iterations=10000,
        )
        assert (
          ei_eval.evaluate_at_point_list(
            numpy.reshape(points_to_sample, (1, ei_eval.num_points_to_sample, ei_eval.dim))
          )[0]
          >= 0
        )

      num_points_to_sample = 3
      num_points_to_evaluate = 6
      points_being_sampled = all_points[:4]
      points_to_sample = domain.generate_quasi_random_points_in_domain(num_points_to_sample * num_points_to_evaluate)
      points_to_sample = points_to_sample.reshape(num_points_to_evaluate, num_points_to_sample, domain.dim)
      ei_eval = ExpectedParallelImprovement(
        gaussian_process,
        num_points_to_sample,
        points_being_sampled=points_being_sampled,
        num_mc_iterations=10000,
      )
      ei_vals = ei_eval.evaluate_at_point_list(points_to_sample)
      assert all(ei_vals >= 0)

  @flaky(max_runs=2)
  def test_qei_accuracy(self, one_hot_domain_list, gaussian_process_list):
    num_points_to_sample = 3
    num_points_being_sampled = 4
    num_random_tests = 30
    mc_iterations_values = [100, 1000, 10000]

    for domain, gaussian_process in zip(
      one_hot_domain_list[:1], gaussian_process_list[:1]
    ):  # Can do more, time permitting
      points_being_sampled = domain.generate_quasi_random_points_in_domain(num_points_being_sampled)
      points_to_sample = domain.generate_quasi_random_points_in_domain(num_points_to_sample)

      ei_eval = ExpectedParallelImprovement(
        gaussian_process,
        num_points_to_sample,
        points_being_sampled=points_being_sampled,
      )
      # pylint: disable=protected-access
      true_result = ei_eval._compute_expected_improvement_qd_analytic(points_to_sample)
      # pylint: enable=protected-access

      std_results = []
      for num_mc_iterations in mc_iterations_values:
        ei_eval.num_mc_iterations = num_mc_iterations

        mc_results = [
          ei_eval.evaluate_at_point_list(
            numpy.reshape(points_to_sample, (1, ei_eval.num_points_to_sample, ei_eval.dim))
          )[0]
          for _ in range(num_random_tests)
        ]
        ei_mean_eapl, ei_std_eapl = numpy.mean(mc_results), numpy.std(mc_results)

        mc_results = [
          ei_eval.evaluate_at_point_list(
            numpy.reshape(points_to_sample, (1, ei_eval.num_points_to_sample, ei_eval.dim))
          )[0]
          for _ in range(num_random_tests)
        ]
        ei_mean_caf, ei_std_caf = numpy.mean(mc_results), numpy.std(mc_results)

        assert abs(ei_mean_eapl - true_result) < 2 * ei_std_eapl
        assert abs(ei_mean_caf - true_result) < 2 * ei_std_caf
        std_results.append(ei_std_eapl)
      assert all(numpy.diff(std_results) < 0) or any(std_results == 0)

  def test_multistart_analytic_expected_improvement_optimization(self):
    """
        Check that multistart optimization (gradient descent) can find the optimum point
        to sample (using 1D analytic EI).
        """
    numpy.random.seed(3148)
    dim = 3
    domain = self.form_continous_and_uniform_domain(dim=dim, lower_element=-2, higher_element=2)
    gaussian_process = self.form_gaussian_process_and_data(domain=domain, num_sampled=50, noise_per_point=0.002)

    tolerance = 1.0e-6

    ei_eval = ExpectedImprovement(gaussian_process)

    # expand the domain so that we are definitely not doing constrained optimization
    expanded_domain = ContinuousDomain([[-4.0, 2.0]] * domain.dim)
    ei_optimizer = AdamOptimizer(
      acquisition_function=ei_eval,
      domain=expanded_domain,
      num_multistarts=100,
      maxiter=1000,
    )
    best_point, _ = ei_optimizer.optimize()

    # Check that gradients are small or that the answer is on a boundary
    gradient = ei_eval.evaluate_grad_at_point_list(numpy.atleast_2d(best_point))
    if not expanded_domain.check_point_on_boundary(best_point, tol=1e-3):
      self.assert_vector_within_relative(gradient, numpy.zeros(gradient.shape), tolerance)

    # Check that output is in the domain
    assert expanded_domain.check_point_acceptable(best_point) is True


class TestExpectedImprovementWithFailures(GaussianProcessTestCase):
  def test_evaluation_probabilistic_failures(
    self,
    one_hot_domain_list,
    gaussian_process_list,
    probabilistic_failures_list,
  ):
    for domain, gp, pf in zip(one_hot_domain_list, gaussian_process_list, probabilistic_failures_list):
      ei = ExpectedImprovement(gp)
      eif = ExpectedImprovementWithFailures(gp, pf)
      pts = domain.generate_quasi_random_points_in_domain(50)
      ei_vals = ei.evaluate_at_point_list(pts)
      pf_vals = pf.compute_probability_of_success(pts)
      eif_vals = eif.evaluate_at_point_list(pts)
      self.assert_vector_within_relative(ei_vals * pf_vals, eif_vals, 1e-13)

  def test_grad_against_finite_difference(
    self,
    one_hot_domain_list,
    gaussian_process_list,
    probabilistic_failures_list,
  ):
    h = 1e-6
    n_test = 50
    for domain, gp, pf in zip(one_hot_domain_list, gaussian_process_list, probabilistic_failures_list):
      eif = ExpectedImprovementWithFailures(gp, pf)
      pts = domain.generate_quasi_random_points_in_domain(n_test)
      self.check_gradient_with_finite_difference(
        pts,
        eif.evaluate_at_point_list,
        eif.evaluate_grad_at_point_list,
        tol=domain.dim * 1e-6,
        fd_step=h * numpy.ones(domain.dim),
      )

  def test_evaluation_product_probabilistic_failures(
    self,
    one_hot_domain_list,
    gaussian_process_list,
    product_of_list_probabilistic_failures_list,
  ):
    for domain, gp, ppf in zip(
      one_hot_domain_list,
      gaussian_process_list,
      product_of_list_probabilistic_failures_list,
    ):
      ei = ExpectedImprovement(gp)
      eif = ExpectedImprovementWithFailures(gp, ppf)
      pts = domain.generate_quasi_random_points_in_domain(50)
      ei_vals = ei.evaluate_at_point_list(pts)
      pf_vals = ppf.compute_probability_of_success(pts)
      eif_vals = eif.evaluate_at_point_list(pts)
      self.assert_vector_within_relative(ei_vals * pf_vals, eif_vals, 1e-13)

  def test_grad_product_against_finite_difference(
    self, one_hot_domain_list, gaussian_process_list, product_of_list_probabilistic_failures_list
  ):
    h = 1e-6
    n_test = 50
    for domain, gp, ppf in zip(
      one_hot_domain_list,
      gaussian_process_list,
      product_of_list_probabilistic_failures_list,
    ):
      eif = ExpectedImprovementWithFailures(gp, ppf)
      pts = domain.generate_quasi_random_points_in_domain(n_test)
      self.check_gradient_with_finite_difference(
        pts,
        eif.evaluate_at_point_list,
        eif.evaluate_grad_at_point_list,
        tol=domain.dim * 1e-6,
        fd_step=h * numpy.ones(domain.dim),
      )
