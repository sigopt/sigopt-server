# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import warnings

import numpy
import scipy.optimize

from libsigopt.compute.misc.constant import L_BFGS_B_OPTIMIZER, SLSQP_OPTIMIZER
from libsigopt.compute.optimization_auxiliary import (
  OPTIMIZATION_PARAMETERS_TO_DEFAULTS,
  LBFGSBParameters,
  OptimizationResults,
  Optimizer,
  SLSQPParameters,
)


MINIMUM_SUCCESSFUL_MULTISTARTS_NUMBER = 0
MINIMUM_SUCCESSFUL_MULTISTARTS_FRACTION = 0
NUM_BACKUP_MULTISTARTS = 1000


class ScipyOptimizable(object):
  """Class that an object must fulfill to be optimized by a _ScipyOptimizerWrapper."""

  @property
  def differentiable(self):
    raise NotImplementedError()

  def get_current_point(self):
    raise NotImplementedError()

  def set_current_point(self, current_point):
    raise NotImplementedError()

  current_point = property(get_current_point, set_current_point)

  def compute_objective_function(self):
    raise NotImplementedError()

  def compute_grad_objective_function(self):
    raise NotImplementedError()


class MultistartOptimizer(Optimizer):
  r"""A general class for multistarting another optimizer."""

  def __init__(self, optimizer, num_multistarts=0, log_sample=False):
    """Construct a MultistartOptimizer for multistarting any implementation of Optimizer."""
    assert not isinstance(optimizer, MultistartOptimizer)
    self.optimizer = optimizer
    self.num_multistarts = num_multistarts
    self.log_sample = log_sample

  def optimize(self, selected_starts=None, **kwargs):
    """Perform multistart optimization with self.optimizer.

        The outcome of this optimization is dependent on the MINIMUM_SUCCESSFUL_MULTISTARTS criteria. Choosing
        num_multistarts == 0 deactivates this criteria, but then requires selected_starts to be passed.

        random_starts can be None or a list of m points at which to multistart:
        If num_multistarts > m, the first m will come from selected_starts and the rest will be randomly chosen.
        If num_multistarts < m, ALL of selected_starts will be used.
          In this setting, num_mulistarts will only be used to create a bound on potential extras needed to
          satisfy the MINIMUM_SUCCESSFUL_MULTISTARTS quota
        If num_multistarts == 0 and selected_starts is None, there will be an error.
        """
    if selected_starts is None:
      if self.num_multistarts < 1:
        raise ValueError("You must either specify starting locations or how many to create randomly.")
      selected_starts = numpy.empty((0, self.optimizer.dim))
    num_extra_starts = self.num_multistarts - len(selected_starts)
    if num_extra_starts <= 0:
      initial_starts = selected_starts
    else:
      extra_starts = self.optimizer.domain.generate_quasi_random_points_in_domain(
        num_extra_starts,
        self.log_sample,
      )
      try:
        initial_starts = numpy.concatenate((selected_starts, extra_starts), axis=0)
      except ValueError as e:
        raise ValueError(f"selected_starts {selected_starts}\n extra_starts {extra_starts}") from e
    backup_starts = self.optimizer.domain.generate_quasi_random_points_in_domain(
      NUM_BACKUP_MULTISTARTS,
      self.log_sample,
    )

    all_starts = numpy.concatenate((initial_starts, backup_starts), axis=0)

    # NOTE: best_point is set to None for initialization, but is updated on the first step of the loop
    # TODO(RTL-62): Debate if there is a better way to deal with scipy solvers that violate the constraints
    best_point = None
    best_function_value = -numpy.inf
    start_list = []
    end_list = []
    function_value_list = []
    successes_list = []
    for point in all_starts:
      try:
        self.optimizer.objective_function.current_point = point
        self.optimizer.optimize(**kwargs)
      except numpy.linalg.LinAlgError:
        function_value = float("nan")
        success = False
      else:
        # The negation here is required because the optimizer decorator has already negated the value
        function_value = -self.optimizer.optimization_results.fun
        success = self.optimizer.optimization_results.success

      end_point = self.optimizer.objective_function.current_point
      if not self.optimizer.domain.check_point_acceptable(end_point):
        function_value = float("nan")
        success = False

      start_list.append(point)
      function_value_list.append(function_value)
      successes_list.append(success)
      end_list.append(end_point)
      if best_point is None or (success and function_value > best_function_value):
        # NOTE: If the optimizer does not satisfy the constraints, use a point that is in the domain.
        if best_point is None and not success:
          best_point = point
          continue
        best_point = end_point
        best_function_value = function_value if not numpy.isnan(function_value) else best_function_value

      if self.num_multistarts == 0:
        if len(function_value_list) == len(selected_starts):
          break
      elif len(function_value_list) >= self.num_multistarts:
        num_successes = sum(successes_list)
        min_num_successes = max(
          MINIMUM_SUCCESSFUL_MULTISTARTS_NUMBER,
          numpy.floor(MINIMUM_SUCCESSFUL_MULTISTARTS_FRACTION * self.num_multistarts),
        )
        if num_successes >= min_num_successes:
          break
    else:
      raise RuntimeError(
        f"{len(all_starts)} multistarts attempted, {sum(successes_list)} succeeded, which was insufficient: "
        f"num_multistarts={self.num_multistarts}, "
        f"minimum required was max({MINIMUM_SUCCESSFUL_MULTISTARTS_NUMBER}, "
        f"{numpy.floor(MINIMUM_SUCCESSFUL_MULTISTARTS_FRACTION * self.num_multistarts)})"
      )

    all_results = OptimizationResults(
      starting_points=numpy.array(start_list),
      ending_points=numpy.array(end_list),
      function_values=numpy.array(function_value_list),
    )
    return best_point, all_results


class _ScipyOptimizerWrapper(Optimizer):
  """Wrapper class to construct an optimizer from scipy optimization methods."""

  # Type of the optimizer_parameters object, specified in subclass
  optimizer_parameters_type = ()
  optimizer_name = None

  def __init__(self, domain, optimizable, optimizer_parameters):
    self.domain = domain
    assert isinstance(optimizable, ScipyOptimizable)
    self.objective_function = optimizable
    self.optimization_results = None

    if optimizer_parameters is None:
      optimizer_parameters = OPTIMIZATION_PARAMETERS_TO_DEFAULTS[self.optimizer_parameters_type]
    if not isinstance(optimizer_parameters, self.optimizer_parameters_type):
      raise TypeError(
        f"optimization_paramters is of type: {optimizer_parameters.__class__},"
        f" expected {self.optimizer_parameters_type}"
      )

    self.optimizer_parameters = optimizer_parameters

  @property
  def dim(self):
    return self.domain.dim

  def joint_function_gradient_eval(self, **kwargs):
    def decorated(point):
      # Very rarely, SLSQP generates all NaN points.
      if numpy.any(numpy.isnan(point)):
        return numpy.inf, numpy.zeros((self.dim,))

      self.objective_function.current_point = point
      value = -self.objective_function.compute_objective_function(**kwargs)
      gradient = -self.objective_function.compute_grad_objective_function(**kwargs)
      assert numpy.isfinite(value) and gradient.shape == (self.dim,)
      return value, gradient

    return decorated

  def _scipy_decorator(self, func, **kwargs):
    def decorated(point):
      self.objective_function.current_point = point
      return -func(**kwargs)

    return decorated

  def optimize(self, **kwargs):
    self.optimization_results = self._optimize(**kwargs)
    point = self.optimization_results.x
    self.objective_function.current_point = point

  def _optimize(self, **kwargs):
    raise NotImplementedError


class LBFGSBOptimizer(_ScipyOptimizerWrapper):
  optimizer_parameters_type = LBFGSBParameters
  optimizer_name = L_BFGS_B_OPTIMIZER

  def __init__(self, domain, optimizable, optimizer_parameters=None):
    super().__init__(domain, optimizable, optimizer_parameters)
    if not (self.objective_function.differentiable or self.optimizer_parameters.approx_grad):
      raise AttributeError("For L-BFGS-B you must either provide the gradient, or request an approximation")

  def _optimize(self, **kwargs):
    options = self.optimizer_parameters.scipy_kwargs()
    approx_grad = options.pop("approx_grad")
    if approx_grad:
      return scipy.optimize.minimize(
        fun=self._scipy_decorator(self.objective_function.compute_objective_function, **kwargs),
        x0=self.objective_function.current_point.flatten(),
        method="L-BFGS-B",
        bounds=self.domain.domain_bounds,
        options=options,
      )
    else:
      options.pop("eps")
      return scipy.optimize.minimize(
        fun=self.joint_function_gradient_eval(**kwargs),
        x0=self.objective_function.current_point.flatten(),
        method="L-BFGS-B",
        jac=True,
        bounds=self.domain.domain_bounds,
        options=options,
      )


class SLSQPOptimizer(_ScipyOptimizerWrapper):
  optimizer_parameters_type = SLSQPParameters
  optimizer_name = SLSQP_OPTIMIZER

  def __init__(self, domain, optimizable, optimizer_parameters=None):
    super().__init__(domain, optimizable, optimizer_parameters)
    if not (self.objective_function.differentiable or self.optimizer_parameters.approx_grad):
      raise AttributeError("For SLSQP you must either provide the gradient, or request an approximation")

  def _optimize(self, **kwargs):
    options = self.optimizer_parameters.scipy_kwargs()
    approx_grad = options.pop("approx_grad")
    if approx_grad:
      return scipy.optimize.minimize(
        fun=self._scipy_decorator(self.objective_function.compute_objective_function, **kwargs),
        x0=self.objective_function.current_point.flatten(),
        method="SLSQP",
        bounds=self.domain.domain_bounds,
        constraints=self.domain.get_constraints_for_scipy(),
        options=options,
      )
    else:
      options.pop("eps")
      with warnings.catch_warnings():
        warnings.filterwarnings(
          action="ignore",
          category=RuntimeWarning,
          message="Values in x were outside bounds during a minimize step, clipping to bounds",
        )
        return scipy.optimize.minimize(
          fun=self.joint_function_gradient_eval(**kwargs),
          x0=self.objective_function.current_point.flatten(),
          method="SLSQP",
          jac=True,
          bounds=self.domain.domain_bounds,
          constraints=self.domain.get_constraints_for_scipy(),
          options=options,
        )
