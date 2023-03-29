# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.compute.acquisition_function import AcquisitionFunction
from libsigopt.compute.domain import ContinuousDomain, FixedIndicesOnContinuousDomain
from libsigopt.compute.misc.constant import ADAM_OPTIMIZER, DE_OPTIMIZER
from libsigopt.compute.optimization_auxiliary import (
  DEFAULT_VECOPT_MAXITER,
  OPTIMIZATION_PARAMETERS_TO_DEFAULTS,
  AdamParameters,
  DEParameters,
  OptimizationResults,
  Optimizer,
)


class VectorizedOptimizer(Optimizer):
  optimizer_name = NotImplemented
  optimizer_parameters_type = NotImplemented

  def __init__(self, domain, acquisition_function, num_multistarts, optimizer_parameters, maxiter):
    """
        This is the base class for vectorized _maximization_.
        """
    assert isinstance(domain, (ContinuousDomain, FixedIndicesOnContinuousDomain))
    self.domain = domain
    assert isinstance(acquisition_function, AcquisitionFunction)
    assert self.dim == acquisition_function.dim * acquisition_function.num_points_to_sample
    self.af = acquisition_function
    assert not self.requires_gradients or self.af.differentiable

    self.num_multistarts = num_multistarts
    self.maxiter = maxiter if maxiter is not None else DEFAULT_VECOPT_MAXITER

    optimizer_parameters = optimizer_parameters or OPTIMIZATION_PARAMETERS_TO_DEFAULTS[self.optimizer_parameters_type]
    # pylint: disable=isinstance-second-argument-not-valid-type
    if not isinstance(optimizer_parameters, self.optimizer_parameters_type):
      raise TypeError(
        f"optimizer_parameters_type is of type: {optimizer_parameters.__class__}",
        f"expecting {self.optimizer_parameters_type}",
      )
    # pylint: enable=isinstance-second-argument-not-valid-type
    self.optimizer_parameters = optimizer_parameters

    # This is information for monitoring progress during the optimization
    # It is private to make sure that it is only updated during evaluate_and_monitor
    self._best_location = None
    self._best_value = None

  def __repr__(self):
    return (
      f"{self.__class__.__name__}"
      f"(optimizer_parameters={self.optimizer_parameters}, "
      f"num_multistarts={self.num_multistarts}, "
      f"maxiter={self.maxiter})"
    )

  @property
  def best_location(self):
    return self._best_location

  @property
  def best_value(self):
    return self._best_value

  @property
  def requires_gradients(self):
    raise NotImplementedError()

  @property
  def dim(self):
    return self.domain.dim

  def restrict_points_to_domain(self, points, viable_point=None):
    return self.domain.restrict_points_to_domain(points, viable_point=viable_point)

  # NOTE: If we want to extract out the AF, we need to build reshaping into the vectorized evaluation
  def evaluate_and_monitor(self, points):
    if self.af.num_points_to_sample > 1:
      points = points.reshape((len(points), self.af.num_points_to_sample, self.dim // self.af.num_points_to_sample))

    gradients = None
    if self.requires_gradients:
      values, gradients = self.af.joint_function_gradient_eval(points)
    else:
      values = self.af.evaluate_at_point_list(points)

    best_index_now = numpy.nanargmax(values)
    best_value_now = values[best_index_now]
    if self.best_value is None or best_value_now > self.best_value:
      self._best_location = points[best_index_now].flatten()
      self._best_value = best_value_now

    return values, gradients

  def optimize(self, selected_starts=None):
    if selected_starts is None:
      starting_points = self.domain.generate_quasi_random_points_in_domain(self.num_multistarts)
    else:
      num_extra_starts = self.num_multistarts - len(selected_starts)
      if num_extra_starts <= 0:
        starting_points = numpy.copy(selected_starts)
      else:
        extra_starts = self.domain.generate_quasi_random_points_in_domain(num_extra_starts)
        starting_points = numpy.concatenate((selected_starts, extra_starts), axis=0)

    # Restrict points makes a copy of starting points and guarantees they are all valid
    restricted_starting_points = self.restrict_points_to_domain(starting_points)
    ending_points = self._optimize(restricted_starting_points)  # restricted_starting_points may change
    values, _ = self.evaluate_and_monitor(ending_points)

    all_results = OptimizationResults(
      starting_points=starting_points,
      ending_points=ending_points,
      function_values=values,
    )
    return self.best_location, all_results

  def _optimize(self, points):
    raise NotImplementedError()


class DEOptimizer(VectorizedOptimizer):
  """
    Implementation of Differential Evolution optimizer, references:
      - Storn and Price, Differential Evolution - a Simple and Efficient Heuristic for Global Optimization over
        Continuous Spaces
    """

  optimizer_name = DE_OPTIMIZER
  optimizer_parameters_type = DEParameters
  requires_gradients = False

  def __init__(self, domain, acquisition_function, num_multistarts, optimizer_parameters=None, maxiter=None):
    super().__init__(domain, acquisition_function, num_multistarts, optimizer_parameters, maxiter)
    self.strategy = self.optimizer_parameters.strategy
    self.mutation = self.optimizer_parameters.mutation
    self.crossover_probability = self.optimizer_parameters.crossover_probability

    # NOTE: This command creates a n x n-1 matrix, where n = num_multistarts, of the following form
    # [[1, 2, 3, ... , n],
    #  [0, 2, 3, ... , n],
    #  [0, 1, 3, ...., n],
    #  ....
    #  [0, 1, 2, ...., n-1]]
    self.index_matrix = numpy.triu(
      numpy.tile(numpy.arange(1, self.num_multistarts, dtype=int), (self.num_multistarts, 1))
    ) + numpy.tril(numpy.tile(numpy.arange(0, self.num_multistarts - 1, dtype=int), (self.num_multistarts, 1)), -1)

    if self.strategy == "rand1bin":
      self.mutation_strat = self._rand1
    if self.strategy == "best1bin":
      self.mutation_strat = self._best1

  def _optimize(self, points):
    self.evaluate_and_monitor(points)
    for _ in range(self.maxiter):
      selection_indices = numpy.random.randint(0, self.num_multistarts - 1, (self.num_multistarts, 3))
      selection_indices = self.index_matrix[numpy.arange(self.num_multistarts)[:, None], selection_indices]
      mutants = self.mutation_strat(points, selection_indices)
      cross_points = numpy.random.random((self.num_multistarts, self.dim)) < self.crossover_probability
      trials = numpy.where(cross_points, mutants, points)

      # makes sure we always evaluate_and_monitor acceptable points
      trials = self.domain.restrict_points_to_domain(trials)
      values_from_trials, _ = self.evaluate_and_monitor(trials)

      trials_which_improved = values_from_trials >= self.best_value
      points[trials_which_improved] = trials[trials_which_improved]
    return points

  def _best1(self, candidates, selection_indices):
    return self.best_location + self.mutation * (
      candidates[selection_indices[:, 0]] - candidates[selection_indices[:, 1]]
    )

  def _rand1(self, candidates, selection_indices):
    return candidates[selection_indices[:, 0]] + self.mutation * (
      candidates[selection_indices[:, 1]] - candidates[selection_indices[:, 2]]
    )


class AdamOptimizer(VectorizedOptimizer):
  """
    Implementation of Adam optimizer, references:
      - Kingma and Ba, Adam - A Method for Stochastic Optimization (http://arxiv.org/abs/1412.6980v8)

    Parameter guidance:
      beta_1: Generally close to 1.
      beta_2: Generally close to 1.
      epsilon: A perturbation factor, small positive number.
    """

  optimizer_name = ADAM_OPTIMIZER
  optimizer_parameters_type = AdamParameters
  requires_gradients = True

  def __init__(self, domain, acquisition_function, num_multistarts, optimizer_parameters=None, maxiter=None):
    super().__init__(domain, acquisition_function, num_multistarts, optimizer_parameters, maxiter)
    self.learning_rate = self.optimizer_parameters.learning_rate
    assert self.learning_rate >= 0
    self.beta_1 = self.optimizer_parameters.beta_1
    assert 0 < self.beta_1 < 1
    self.beta_2 = self.optimizer_parameters.beta_2
    assert 0 < self.beta_2 < 1
    self.epsilon = self.optimizer_parameters.epsilon
    assert self.epsilon >= 0

  def _optimize(self, points):
    first_moment = numpy.zeros(self.dim)
    second_moment = numpy.zeros(self.dim)
    for i in range(1, self.maxiter):
      _, gradients = self.evaluate_and_monitor(points)
      ascend_gradients = -gradients
      first_moment = self.beta_1 * first_moment + (1 - self.beta_1) * ascend_gradients
      second_moment = self.beta_2 * second_moment + (1 - self.beta_2) * ascend_gradients**2
      first_moment_unbiased = first_moment / (1 - self.beta_1**i)
      second_moment_unbiased = second_moment / (1 - self.beta_2**i)
      update = -self.learning_rate * first_moment_unbiased / (numpy.sqrt(second_moment_unbiased) + self.epsilon)
      next_points = points + update
      points = self.restrict_points_to_domain(next_points)
    return points
