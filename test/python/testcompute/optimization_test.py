# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Tests for the Python optimization module (null, gradient descent, and multistarting) using a simple polynomial
objective."""

import numpy
import pytest

from libsigopt.compute.domain import DEFAULT_SAFETY_MARGIN_FOR_CONSTRAINTS, ContinuousDomain
from libsigopt.compute.optimization import LBFGSBOptimizer, MultistartOptimizer, ScipyOptimizable, SLSQPOptimizer
from libsigopt.compute.optimization_auxiliary import (
  DEFAULT_LBFGSB_PARAMETERS,
  DEFAULT_SLSQP_PARAMETERS,
  LBFGSBParameters,
  SLSQPParameters,
)
from testaux.numerical_test_case import NumericalTestCase


# customlint: disable=AccidentalFormatStringRule


class QuadraticFunction(ScipyOptimizable):
  r"""Class to evaluate the function f(x_1,...,x_{dim}) = -\sum_i (x_i - s_i)^2, i = 1..dim.

    This is a simple quadratic form with maxima at (s_1, ..., s_{dim}).

    """

  def __init__(self, maxima_point, current_point):
    """Create an instance of QuadraticFunction with the specified maxima."""
    self._maxima_point = numpy.copy(maxima_point)
    self._current_point = numpy.copy(current_point)

  @property
  def dim(self):
    """Return the number of spatial dimensions."""
    return self._maxima_point.size

  @property
  def optimum_value(self):
    """Return max_x f(x), the global maximum value of this function."""
    return 0.0

  @property
  def optimum_point(self):
    """Return the argmax_x (f(x)), the point at which the global maximum occurs."""
    return numpy.copy(self._maxima_point)

  @property
  def differentiable(self):
    return True

  def get_current_point(self):
    return numpy.copy(self._current_point)

  def set_current_point(self, current_point):
    self._current_point = numpy.copy(current_point)

  current_point = property(get_current_point, set_current_point)

  def compute_objective_function(self):
    temp = self._current_point - self._maxima_point
    temp *= temp
    return -temp.sum()

  def compute_grad_objective_function(self):
    return -2.0 * (self._current_point - self._maxima_point)


class TestOptimizer(NumericalTestCase):
  @classmethod
  @pytest.fixture(autouse=True, scope="class")
  def base_setup(cls):
    return cls._base_setup()

  @classmethod
  def _base_setup(cls):
    """Set up a test case for optimizing a simple quadratic polynomial."""
    cls.dim = 3
    domain_bounds = [[-1.0, 1.0]] * cls.dim
    cls.domain = ContinuousDomain(domain_bounds)

    large_domain_bounds = [[-1.0, 1.0]] * cls.dim
    cls.large_domain = ContinuousDomain(large_domain_bounds)

    maxima_point = numpy.full(cls.dim, 0.5)
    current_point = numpy.zeros(cls.dim)
    cls.polynomial = QuadraticFunction(maxima_point, current_point)

  def test_lbfgsb_default_parameters(self):
    default_parameters = LBFGSBParameters(
      approx_grad=False,
      eps=1.0e-8,
      ftol=1.0e-4,
      maxfun=15000,
      maxcor=10,
      gtol=1.0e-4,
    )
    assert default_parameters == LBFGSBParameters()

  def test_slsqp_default_parameters(self):
    default_parameters = SLSQPParameters(
      approx_grad=False,
      eps=1.0e-8,
      maxiter=150,
      ftol=1.0e-4,
    )
    assert default_parameters == SLSQPParameters()

  def test_slsqp_optimizer_bounded(self):
    # Domain where the optimum, (0.5, 0.5, 0.5), lies outside the domain
    domain_bounds = [[0.05, 0.32], [0.05, 0.6], [0.05, 0.32]]
    domain = ContinuousDomain(domain_bounds)
    slsqp_optimizer = SLSQPOptimizer(domain, self.polynomial, DEFAULT_SLSQP_PARAMETERS)

    # Work out what the maxima point woudl be given the domain constraints
    # (i.e., project to the nearest point on domain)
    bounded_optimum_point = self.polynomial.optimum_point
    for i, bounds in enumerate(domain_bounds):
      if bounded_optimum_point[i] > bounds[1]:
        bounded_optimum_point[i] = bounds[1]
      elif bounded_optimum_point[i] < bounds[0]:
        bounded_optimum_point[i] = bounds[0]

    tolerance = 5.0e-9
    initial_guess = numpy.full(self.polynomial.dim, 0.2)
    slsqp_optimizer.objective_function.current_point = initial_guess
    initial_value = slsqp_optimizer.objective_function.compute_objective_function()
    slsqp_optimizer.optimize()
    output = slsqp_optimizer.objective_function.current_point
    # Verify coordinates
    self.assert_vector_within_relative_norm(output, bounded_optimum_point, tolerance)

    # Verify optimized value is better than initial guess
    final_value = self.polynomial.compute_objective_function()
    assert final_value >= initial_value

    # Verify derivative: only get 0 derivative if the coordinate lies inside domain boundaries
    gradient = self.polynomial.compute_grad_objective_function()
    for i, bounds in enumerate(domain_bounds):
      if bounds[0] <= self.polynomial.optimum_point[i] <= bounds[1]:
        self.assert_scalar_within_relative(gradient[i], 0.0, tolerance)

  def test_slsqp_optimizer_constrained(self):
    domain_bounds = [[0, 1], [0, 1], [0, 1]]
    domain = ContinuousDomain(domain_bounds)
    domain.set_constraint_list([{"weights": numpy.array([-1, -1, -1]), "rhs": -1.6}])
    slsqp_optimizer = SLSQPOptimizer(domain, self.polynomial, DEFAULT_SLSQP_PARAMETERS)

    constrained_optimum_point = self.polynomial.optimum_point

    tolerance = 5.0e-9
    initial_guess = numpy.full(self.polynomial.dim, 0.2)
    slsqp_optimizer.objective_function.current_point = initial_guess
    initial_value = slsqp_optimizer.objective_function.compute_objective_function()
    slsqp_optimizer.optimize()
    output = slsqp_optimizer.objective_function.current_point
    assert domain.check_point_acceptable(output)
    # Verify coordinates
    self.assert_vector_within_relative_norm(
      output,
      constrained_optimum_point,
      tolerance,
    )

    # Verify optimized value is better than initial guess
    final_value = self.polynomial.compute_objective_function()
    assert final_value >= initial_value

    # Verify derivative is 0
    gradient = self.polynomial.compute_grad_objective_function()
    for i in range(domain.dim):
      self.assert_scalar_within_relative(gradient[i], 0.0, tolerance)

    # set global optimal to be outside of feasible region
    domain.set_constraint_list([{"weights": numpy.array([-1, -1, -1]), "rhs": -1}])
    slsqp_optimizer = SLSQPOptimizer(domain, self.polynomial, DEFAULT_SLSQP_PARAMETERS)

    constrained_optimum_point = numpy.full_like(self.polynomial.optimum_point, 1 / 3)

    tolerance = 5.0e-9
    initial_guess = numpy.full(self.polynomial.dim, 0.2)
    slsqp_optimizer.objective_function.current_point = initial_guess
    initial_value = slsqp_optimizer.objective_function.compute_objective_function()
    slsqp_optimizer.optimize()
    output = slsqp_optimizer.objective_function.current_point
    assert domain.check_point_acceptable(output)
    self.assert_vector_within_relative_norm(
      output,
      constrained_optimum_point,
      DEFAULT_SAFETY_MARGIN_FOR_CONSTRAINTS,
    )

    final_value = self.polynomial.compute_objective_function()
    assert final_value >= initial_value

  def test_multistarted_slsqp_optimizer_crippled(self):
    """Confirm that an error will occur if the problem is unsolved, but not when it is solved."""
    slsqp_parameters_crippled = SLSQPParameters(maxiter=1)
    slsqp_optimizer_crippled = SLSQPOptimizer(self.domain, self.polynomial, slsqp_parameters_crippled)

    num_points = 15
    points = self.domain.generate_quasi_random_points_in_domain(num_points)

    multistart_optimizer = MultistartOptimizer(slsqp_optimizer_crippled, num_points)
    with pytest.raises(RuntimeError):
      multistart_optimizer.optimize(selected_starts=points)
      raise RuntimeError  # Just while we have deactivated the optimization monitoring

    points_with_opt = numpy.append(points, self.polynomial.optimum_point.reshape((1, self.polynomial.dim)), axis=0)
    slsqp_optimizer_okay = SLSQPOptimizer(self.domain, self.polynomial, DEFAULT_SLSQP_PARAMETERS)
    multistart_optimizer = MultistartOptimizer(slsqp_optimizer_okay, 0)
    test_best_point, _ = multistart_optimizer.optimize(selected_starts=points_with_opt)
    # This optimizer should be able to find the exact answer since it was included
    for value in test_best_point - self.polynomial.optimum_point:
      assert value == 0.0

  @pytest.mark.parametrize(
    "optimizer_class, optimizer_parameters",
    [
      (LBFGSBOptimizer, DEFAULT_LBFGSB_PARAMETERS),
      (SLSQPOptimizer, DEFAULT_SLSQP_PARAMETERS),
    ],
  )
  def test_optimizer(self, optimizer_class, optimizer_parameters, tolerance=2.0e-13 * 1e6):
    """Check that the optimizer can find the optimum of the quadratic test objective."""
    # Check the claimed optima is an optima
    optimum_point = self.polynomial.optimum_point
    self.polynomial.current_point = optimum_point
    gradient = self.polynomial.compute_grad_objective_function()
    self.assert_vector_within_relative(gradient, numpy.zeros(self.polynomial.dim), 0.0)

    # Verify that the optimizer does not move from the optima if we start it there.
    optimizer = optimizer_class(self.domain, self.polynomial, optimizer_parameters)
    optimizer.optimize()
    output = optimizer.objective_function.current_point
    self.assert_vector_within_relative(output, optimum_point, 2.0 * numpy.finfo(numpy.float64).eps)

    # Start at a wrong point and check optimization
    initial_guess = numpy.full(self.polynomial.dim, 0.2)
    optimizer.objective_function.current_point = initial_guess
    optimizer.optimize()
    output = optimizer.objective_function.current_point
    # Verify coordinates
    self.assert_vector_within_relative(output, optimum_point, tolerance)

    # Verify function value
    value = self.polynomial.compute_objective_function()
    self.assert_scalar_within_relative(value, self.polynomial.optimum_value, tolerance)

    # Verify derivative
    gradient = self.polynomial.compute_grad_objective_function()
    self.assert_vector_within_relative(gradient, numpy.zeros(self.polynomial.dim), tolerance)

  @pytest.mark.parametrize(
    "optimizer_class, optimizer_parameters",
    [
      (LBFGSBOptimizer, DEFAULT_LBFGSB_PARAMETERS),
      (SLSQPOptimizer, DEFAULT_SLSQP_PARAMETERS),
    ],
  )
  def test_multistarted_optimizer(self, optimizer_class, optimizer_parameters):
    """Check that the multistarted optimizer can find the optimum in a 'very' large domain."""
    tolerance = 1.0e-8
    num_points = 30
    optimizer = optimizer_class(self.large_domain, self.polynomial, optimizer_parameters)
    multistart_optimizer = MultistartOptimizer(optimizer, num_points)

    output, all_results = multistart_optimizer.optimize()
    # Verify coordinates
    self.assert_vector_within_relative(output, self.polynomial.optimum_point, tolerance)

    # Verify function value
    self.polynomial.current_point = output
    value = self.polynomial.compute_objective_function()
    self.assert_scalar_within_relative(value, self.polynomial.optimum_value, tolerance)

    # Verify derivative
    gradient = self.polynomial.compute_grad_objective_function()
    self.assert_vector_within_relative(gradient, numpy.zeros(self.polynomial.dim), tolerance)

    # Verify all the results have been recorded for each category
    assert len(all_results.starting_points) == len(all_results.ending_points) == len(all_results.function_values)

    # Verify the answers from each multistart were inside the domain
    assert all(optimizer.domain.check_point_acceptable(x) for x in all_results.ending_points)
