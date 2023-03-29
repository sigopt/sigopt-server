# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import dataclass

import numpy
from scipy.stats import multivariate_normal, norm

from libsigopt.compute.acquisition_function import AcquisitionFunction
from libsigopt.compute.probabilistic_failures import ProbabilisticFailuresBase, ProductOfListOfProbabilisticFailures
from libsigopt.compute.python_utils import compute_cholesky_for_gp_sampling


# These number is defined based on certain bounds we currently have in place ... should be handled more intelligently
DEFAULT_MC_ITERATIONS_TOTAL_QEI = 10000
DEFAULT_MC_ITERATIONS_PER_LOOP_QEI = 1000
DEFAULT_MC_ITERATIONS_TOTAL_QEIWF = 4000
DEFAULT_MC_ITERATIONS_PER_LOOP_QEIWF = 1000

# Quantile from inteval <0.5, 1> that should be used for Augmented Expected Improvement
AUGMENTED_EI_QUANTILE = 0.75

MINIMUM_ACCEPTABLE_FAILURE_BEST_POINT_PROBABILITY = 0.5


@dataclass(frozen=True, slots=True)
class PenaltyComponents:
  penalty: numpy.ndarray
  grad_penalty: numpy.ndarray


class ExpectedImprovement(AcquisitionFunction):
  def _evaluate_at_point_list(self, points_to_evaluate):
    return self._evaluate_at_point_list_normalized(self.compute_core_components(points_to_evaluate, "func"))

  def _evaluate_at_point_list_normalized(self, core_components):
    return core_components.sqrt_var * numpy.fmax(0.0, core_components.z * core_components.cdf_z + core_components.pdf_z)

  # This function leverages d/dx pdf(x) = -x pdf(x) as well as d/dx cdf(x) = pdf(x)
  def _evaluate_grad_at_point_list(self, points_to_evaluate):
    return self._evaluate_grad_at_point_list_normalized(self.compute_core_components(points_to_evaluate, "grad"))

  def _evaluate_grad_at_point_list_normalized(self, core_components):
    return (
      core_components.grad_sqrt_var * core_components.pdf_z[:, None]
      - core_components.grad_mean * core_components.cdf_z[:, None]
    )

  def joint_function_gradient_eval(self, points_to_evaluate):
    core_components = self.compute_core_components(points_to_evaluate, "both")
    ei = self._evaluate_at_point_list_normalized(core_components)
    ei_grad = self._evaluate_grad_at_point_list_normalized(core_components)
    return ei, ei_grad

  def _append_lie_locations(self, lie_locations):
    self.predictor.append_lie_data(lie_locations)


class ExpectedImprovementWithPenalty(ExpectedImprovement):
  """
    This class allows for penalizing EI values multiplicatively, i.e., EIP(x) = EI(x) * penalty(x)
    """

  def _evaluate_penalty(self, core_components, option):
    raise NotImplementedError()

  def _evaluate_at_point_list(self, points_to_evaluate):
    core_components = self.compute_core_components(points_to_evaluate, "func")
    penalty_components = self._evaluate_penalty(core_components, "func")
    return self._evaluate_at_point_list_penalty(core_components, penalty_components)

  def _evaluate_at_point_list_penalty(self, core_components, penalty_components):
    ei = self._evaluate_at_point_list_normalized(core_components)
    return ei * penalty_components.penalty

  def _evaluate_grad_at_point_list(self, points_to_evaluate):
    core_components = self.compute_core_components(points_to_evaluate, "grad")
    penalty_components = self._evaluate_penalty(core_components, "grad")
    return self._evaluate_grad_at_point_list_penalty(core_components, penalty_components)

  def _evaluate_grad_at_point_list_penalty(self, core_components, penalty_components):
    ei = self._evaluate_at_point_list_normalized(core_components)
    ei_grad = self._evaluate_grad_at_point_list_normalized(core_components)
    return ei_grad * penalty_components.penalty[:, None] + ei[:, None] * penalty_components.grad_penalty

  def joint_function_gradient_eval(self, points_to_evaluate):
    core_components = self.compute_core_components(points_to_evaluate, "both")
    penalty_components = self._evaluate_penalty(core_components, "both")
    ei = self._evaluate_at_point_list_penalty(core_components, penalty_components)
    ei_grad = self._evaluate_grad_at_point_list_penalty(core_components, penalty_components)
    return ei, ei_grad


# TODO(RTL-131): See how this scales with N and D
class AugmentedExpectedImprovement(ExpectedImprovementWithPenalty):
  """
    This is implementation of Augmented Expected Improvement introduced in Huang et al., 2006.
    (https://pdfs.semanticscholar.org/0c51/104c58c3e05f487d87ee94ce2e3b2d11dce6.pdf)
    For more info and formulas see:
    "Noisy kriging-based optimization methods: a unified implementation within the DiceOptim package"

    NOTE: Method is somewhat slower than simple EI, so we should switch it on only after certain level of noise.
    TODO(RTL-32): Check if the +/- situation for quantiles matches up with the minimization
    """

  def __init__(self, predictor):
    super().__init__(predictor)
    mean, var = self.predictor.compute_mean_and_variance_of_points(self.predictor.points_sampled)
    quantiles_values = mean + norm.ppf(AUGMENTED_EI_QUANTILE) * numpy.sqrt(var)

    # TODO(RTL-132): Think about tie-breakers - for example posterior variance to encourage exploration
    best_index = numpy.argmin(quantiles_values)
    self.best_value = mean[best_index]
    self.best_location = self.predictor.points_sampled[best_index, :]
    # We decide to use mean of sample variances for global reported variance, it can be changed if there is better way
    self.noise_variance = numpy.mean(self.predictor.points_sampled_noise_variance)

  def _evaluate_penalty(self, core_components, option):
    grad_penalty = None
    adjusted_var = core_components.var + self.noise_variance
    sqrt_noise_to_signal_ratio = numpy.sqrt(self.noise_variance / adjusted_var)
    penalty = 1 - sqrt_noise_to_signal_ratio
    if option in ("grad", "both"):
      grad_penalty = 0.5 * (sqrt_noise_to_signal_ratio / adjusted_var)[:, None] * core_components.grad_var
    return PenaltyComponents(penalty, grad_penalty)


# TODO(RTL-33): Think on if possible to have a joint failures/augmented model, or how easily that can be done
class ExpectedImprovementWithFailures(ExpectedImprovementWithPenalty):
  def __init__(self, predictor, failure_model):
    assert isinstance(failure_model, ProbabilisticFailuresBase)
    super().__init__(predictor)
    self.failure_model = failure_model
    assert self.failure_model.dim == self.dim, f"failure_model dim: {self.failure_model.dim} != dim of EI: {self.dim}"
    self.gaussian_process = self.predictor
    self.best_location, self.best_value = self._get_best_location_value_not_failure()

  @property
  def differentiable(self):
    return self.gaussian_process.differentiable and self.failure_model.differentiable

  def _get_best_location_value_not_failure(self):
    failure_probs = self.failure_model.compute_probability_of_success(self.gaussian_process.points_sampled)
    acceptable_points_idx = failure_probs > MINIMUM_ACCEPTABLE_FAILURE_BEST_POINT_PROBABILITY
    if not numpy.any(acceptable_points_idx):
      return self.best_location, self.best_value

    acceptable_points = self.gaussian_process.points_sampled[acceptable_points_idx, :]
    acceptable_values = self.gaussian_process.points_sampled_value[acceptable_points_idx]
    best_index = numpy.argmin(acceptable_values)
    return acceptable_points[best_index, :], acceptable_values[best_index]

  def _evaluate_penalty(self, core_components, option):
    if option in ("grad", "both"):
      return PenaltyComponents(*self.failure_model.joint_function_gradient_eval(core_components.x))
    return PenaltyComponents(self.failure_model.compute_probability_of_success(core_components.x), None)


class ExpectedParallelImprovement(AcquisitionFunction):
  def __init__(
    self,
    predictor,
    num_points_to_sample,
    points_being_sampled=None,
    num_mc_iterations=DEFAULT_MC_ITERATIONS_TOTAL_QEI,
    num_mc_iterations_per_loop=DEFAULT_MC_ITERATIONS_PER_LOOP_QEI,
  ):
    """Construct an ExpectedImprovement object that supports q,p-EI."""
    super().__init__(predictor)
    assert int(num_mc_iterations) == num_mc_iterations > 0
    self.num_mc_iterations = num_mc_iterations
    assert int(num_mc_iterations_per_loop) == num_mc_iterations_per_loop > 0
    self.num_mc_iterations_per_loop = num_mc_iterations_per_loop

    assert int(num_points_to_sample) == num_points_to_sample >= 0
    self.num_points_to_sample = num_points_to_sample
    self.points_to_sample = None
    if self.num_points_to_sample == 0:
      self.points_to_sample = numpy.empty((0, self.dim))

    self.points_being_sampled = numpy.empty((0, self.dim))
    if not (points_being_sampled is None or len(points_being_sampled) == 0):
      self.points_being_sampled = numpy.copy(points_being_sampled)

    points_being_sampled_shape = self.points_being_sampled.shape
    assert len(points_being_sampled_shape) == 2, "Points must be passed as 2D arrays"
    assert points_being_sampled_shape[1] == self.dim, "Points must match the GP dimension"

  @property
  def differentiable(self):
    return False

  @property
  def num_points_being_sampled(self):
    return len(self.points_being_sampled)

  # NOTE: Check if, under certain shapes, einsum is more efficient than tensordot
  def _evaluate_at_point_list(self, points_to_evaluate):
    eval_shape = points_to_evaluate.shape
    if len(eval_shape) == 2:  # This is the setting where this was called with a list of points and num_to_sample == 1
      points_to_evaluate = points_to_evaluate[:, None, :]
      eval_shape = points_to_evaluate.shape
    num_to_evaluate, num_to_sample, dim = eval_shape
    assert num_to_sample == self.num_points_to_sample and dim == self.dim
    covariance_size = self.num_points_to_sample + self.num_points_being_sampled

    chol_cov_tensor = numpy.empty((covariance_size, covariance_size, num_to_evaluate))
    for k in range(num_to_evaluate):
      union_of_points = numpy.concatenate((points_to_evaluate[k, :, :], self.points_being_sampled), axis=0)
      cov_mat = self.predictor.compute_covariance_of_points(union_of_points)
      chol_cov_tensor[:, :, k] = compute_cholesky_for_gp_sampling(cov_mat)

    mean_to_evaluate = self.predictor.compute_mean_of_points(numpy.concatenate(points_to_evaluate, axis=0))
    mean_to_evaluate = numpy.reshape(mean_to_evaluate, (num_to_evaluate, num_to_sample)).T

    if self.num_points_being_sampled:
      mean_being_sampled = self.predictor.compute_mean_of_points(self.points_being_sampled)

    num_mc_iterations_per_loop = min(self.num_mc_iterations_per_loop, self.num_mc_iterations)
    result = numpy.zeros(num_to_evaluate)
    num_mc_iterations_executed = 0
    while num_mc_iterations_executed < self.num_mc_iterations:
      normals = numpy.random.normal(size=(num_mc_iterations_per_loop, covariance_size))
      posterior_predictions = numpy.tensordot(chol_cov_tensor, normals, [[1], [1]])
      posterior_predictions[:num_to_sample, :, :] += self.best_value - mean_to_evaluate[:, :, None]

      if self.num_points_being_sampled:
        posterior_predictions[-self.num_points_being_sampled :, :, :] += (
          self.best_value - mean_being_sampled[:, None, None]
        )

      result += numpy.sum(numpy.fmax(0.0, numpy.amax(posterior_predictions, axis=0)), axis=1)
      num_mc_iterations_executed += num_mc_iterations_per_loop
    return result / num_mc_iterations_executed

  def _compute_expected_improvement_qd_analytic(self, points_to_sample):
    """This function is quite slow and is only used for testing the validity of _evaluate_at_point_list

        See Chevalier, and Ginsbourger (2012) for an explanation of it.
        """
    # Since points_being_sampled has already been included here, we do not add it to `num_points`
    union_of_points = numpy.concatenate((points_to_sample, self.points_being_sampled), axis=0)
    mu_star = self.predictor.compute_mean_of_points(union_of_points)
    var_star = self.predictor.compute_covariance_of_points(union_of_points)
    num_points = len(mu_star)
    best_so_far = self.best_value

    def singlevar_norm_pdf(mean, var, param):
      """PDF of univariate Gaussian centered at m with variance var."""
      return norm.pdf(param, mean, numpy.sqrt(var))

    def multivar_norm_cdf(upper, cov_matrix):
      """CDF of multivariate Gaussian centered at 0 with covariance matrix cov_matrix.
         CDF is taken from -inf to u.
         """
      if upper.size == 1:
        return norm.cdf(upper[0], 0, numpy.sqrt(cov_matrix[0, 0]))

      return multivariate_normal.cdf(
        x=upper,
        mean=None,
        cov=cov_matrix,
        maxpts=20000 * upper.size,
        releps=1.0e-9,
        abseps=1.0e-9,
      )

    # Calculation of outer sum (from Proposition 2, equation 3)
    # Although the paper describes a minimization, we can achieve a maximization by inverting m_k and b_k, and then the
    # probability term, as labeled below with 'min'.
    expected_improvement = 0
    for k in range(num_points):
      # Calculation of m_k, which is the mean of Z_k introduced in Proposition 2
      m_k = mu_star - mu_star[k]
      m_k[k] = -mu_star[k]
      m_k = -m_k  # min

      b_k = numpy.zeros(num_points)
      b_k[k] = -best_so_far
      b_k = -b_k  # min

      # Calculation of cov_k, which is the covariance matrix of Z_k introduced in Proposition 2
      # Matrix of cov(Y_j - Y_k, Y_i - Y_k) for i, j != k and cov(Y_j - Y_k, Y_i) for i = k.
      # Calculated using linearity of covariance:
      # cov(Y_j - Y_k, Y_i - Y_k) = cov(Y_i, Y_j) - cov(Y_i, Y_k) - cov(Y_j, Y_k) + cov(Y_k, Y_k)
      cov_k = var_star + var_star[k, k]
      cov_k = cov_k - var_star[..., k]
      cov_k = cov_k - var_star[..., k].reshape(num_points, 1)

      # When i or j = k, then
      # cov(Y_j - Y_k, -Y_k) = cov(Y_k, Y_k) - cov(Y_j, Y_k)
      cov_k[k, ...] = -var_star[..., k] + var_star[k, k]
      cov_k[..., k] = -var_star[..., k] + var_star[k, k]

      # Finally, when i and j = k, we have cov(Y_k, Y_k)
      cov_k[k, k] = var_star[k, k]

      prob_term = (mu_star[k] - best_so_far) * multivar_norm_cdf(b_k - m_k, cov_k)
      prob_term = -prob_term  # min

      # Calculation of inner sum
      sum_term = 0
      if num_points == 1:
        sum_term += cov_k[0, k] * singlevar_norm_pdf(m_k[0], cov_k[0, 0], b_k[0])
      else:
        for i in range(num_points):
          index_no_i = list(range(0, i)) + list(range(i + 1, num_points))

          # c_k introduced on top of page 4
          c_k = (b_k - m_k) - (b_k[i] - m_k[i]) * cov_k[i, :] / cov_k[i, i]
          c_k = c_k[index_no_i]

          # cov_k_no_i introduced on top of page 4
          cov_k_no_i = cov_k - numpy.outer(cov_k[i, :], cov_k[i, :]) / cov_k[i, i]
          cov_k_no_i = cov_k_no_i[index_no_i, ...][..., index_no_i]

          sum_term += cov_k[i, k] * singlevar_norm_pdf(m_k[i], cov_k[i, i], b_k[i]) * multivar_norm_cdf(c_k, cov_k_no_i)

      expected_improvement += prob_term + sum_term
    if not numpy.isfinite(expected_improvement):
      raise RuntimeError("Expected improvement not finite. Variance matrix may be singular.")
    return numpy.fmax(0.0, expected_improvement)


class ExpectedParallelImprovementWithFailures(ExpectedParallelImprovement):
  def __init__(
    self,
    predictor,
    num_points_to_sample,
    failure_model,
    points_being_sampled=None,
    num_mc_iterations=DEFAULT_MC_ITERATIONS_TOTAL_QEIWF,
    num_mc_iterations_per_loop=DEFAULT_MC_ITERATIONS_PER_LOOP_QEIWF,
  ):
    super().__init__(
      predictor,
      num_points_to_sample,
      points_being_sampled,
      num_mc_iterations=num_mc_iterations,
      num_mc_iterations_per_loop=num_mc_iterations_per_loop,
    )
    assert isinstance(failure_model, ProductOfListOfProbabilisticFailures)
    self.failure_model = failure_model
    self.gaussian_process = self.predictor

    self.best_location, self.best_value = self._get_best_location_value_not_failure()

  def _get_best_location_value_not_failure(self):
    failure_probs = self.failure_model.compute_probability_of_success(self.gaussian_process.points_sampled)
    acceptable_points_idx = failure_probs > MINIMUM_ACCEPTABLE_FAILURE_BEST_POINT_PROBABILITY
    if not numpy.any(acceptable_points_idx):
      return self.best_location, self.best_value

    acceptable_points = self.gaussian_process.points_sampled[acceptable_points_idx, :]
    acceptable_values = self.gaussian_process.points_sampled_value[acceptable_points_idx]
    best_index = numpy.argmin(acceptable_values)
    return acceptable_points[best_index, :], acceptable_values[best_index]

  @property
  def differentiable(self):
    return False

  def _evaluate_at_point_list(self, points_to_evaluate):
    eval_shape = points_to_evaluate.shape
    if len(eval_shape) == 2:
      points_to_evaluate = points_to_evaluate[:, None, :]
      eval_shape = points_to_evaluate.shape
    num_to_evaluate, num_to_sample, dim = eval_shape
    assert num_to_sample == self.num_points_to_sample and dim == self.dim
    covariance_size = self.num_points_to_sample + self.num_points_being_sampled

    chol_cov_tensor = numpy.empty((covariance_size, covariance_size, num_to_evaluate))
    chol_cov_tensor_failures = numpy.empty(
      (
        self.failure_model.num_pfs,
        covariance_size,
        covariance_size,
        num_to_evaluate,
      )
    )
    for k in range(num_to_evaluate):
      union_of_points = numpy.concatenate((points_to_evaluate[k, :, :], self.points_being_sampled), axis=0)
      cov_mat = self.gaussian_process.compute_covariance_of_points(union_of_points)
      chol_cov_tensor[:, :, k] = compute_cholesky_for_gp_sampling(cov_mat)
      for i, pf in enumerate(self.failure_model.list_of_probabilistic_failures):
        cov_mat = pf.predictor.compute_covariance_of_points(union_of_points)
        chol_cov_tensor_failures[i, :, :, k] = compute_cholesky_for_gp_sampling(cov_mat)

    mean_to_evaluate = self.gaussian_process.compute_mean_of_points(numpy.concatenate(points_to_evaluate, axis=0))
    mean_to_evaluate = numpy.reshape(mean_to_evaluate, (num_to_evaluate, num_to_sample)).T
    mean_to_evaluate_failures = numpy.empty(
      (
        self.failure_model.num_pfs,
        num_to_sample,
        num_to_evaluate,
      )
    )
    for i, pf in enumerate(self.failure_model.list_of_probabilistic_failures):
      mean_to_evaluate_failures[i] = numpy.reshape(
        pf.predictor.compute_mean_of_points(numpy.concatenate(points_to_evaluate, axis=0)),
        (num_to_evaluate, num_to_sample),
      ).T

    if self.num_points_being_sampled:
      mean_being_sampled = self.gaussian_process.compute_mean_of_points(self.points_being_sampled)
      mean_being_sampled_failures = numpy.empty((self.failure_model.num_pfs, len(self.points_being_sampled)))
      for i, pf in enumerate(self.failure_model.list_of_probabilistic_failures):
        mean_being_sampled_failures[i] = pf.predictor.compute_mean_of_points(self.points_being_sampled)

    num_mc_iterations_per_loop = min(self.num_mc_iterations_per_loop, self.num_mc_iterations)
    result = numpy.zeros(num_to_evaluate)
    num_mc_iterations_executed = 0
    while num_mc_iterations_executed < self.num_mc_iterations:
      normals = numpy.random.normal(size=(num_mc_iterations_per_loop, covariance_size))

      posterior_predictions = numpy.tensordot(chol_cov_tensor, normals, [[1], [1]])
      posterior_predictions[: self.num_points_to_sample, :, :] += mean_to_evaluate[:, :, None]
      # TODO(RTL-36): investigate if these can be rewritten to be more efficient.
      if self.num_points_being_sampled:
        posterior_predictions[-self.num_points_being_sampled :, :, :] += mean_being_sampled[:, None, None]
      # TODO(RTL-37): investigate which direction is best for this 4D tensor.
      posterior_predictions_failures = numpy.zeros(
        (
          self.failure_model.num_pfs,
          covariance_size,
          num_to_evaluate,
          num_mc_iterations_per_loop,
        )
      )
      for i, pf in enumerate(self.failure_model.list_of_probabilistic_failures):
        posterior_predictions_failures[i] = numpy.tensordot(chol_cov_tensor_failures[i], normals, [[1], [1]])
        posterior_predictions_failures[i, : self.num_points_to_sample, :, :] += mean_to_evaluate_failures[i, :, :, None]
        if self.num_points_being_sampled:
          posterior_predictions_failures[i, -self.num_points_being_sampled :, :, :] += (
            mean_being_sampled_failures[i, :, None, None]
          )

      posterior_improvement_predictions = self.best_value - posterior_predictions
      posterior_predictions_failures_product = numpy.ones_like(posterior_improvement_predictions)
      for i, pf in enumerate(self.failure_model.list_of_probabilistic_failures):
        posterior_predictions_failures_product *= posterior_predictions_failures[i] < pf.threshold

      posterior_improvement_predictions_not_failures = (
        posterior_improvement_predictions * posterior_predictions_failures_product
      )

      max_improvement = numpy.fmax(0.0, numpy.amax(posterior_improvement_predictions_not_failures, axis=0))
      if numpy.sum(max_improvement) == 0:
        success_prob = self.failure_model.compute_probability_of_success(points_to_evaluate[:, 0, :])
        posterior_improvement_predictions_not_failures = posterior_improvement_predictions * success_prob[None, :, None]
        max_improvement = numpy.fmax(0.0, numpy.amax(posterior_improvement_predictions_not_failures, axis=0))
      contribution_this_loop = numpy.sum(max_improvement, axis=1)
      result += contribution_this_loop
      num_mc_iterations_executed += num_mc_iterations_per_loop
    return result / num_mc_iterations_executed
