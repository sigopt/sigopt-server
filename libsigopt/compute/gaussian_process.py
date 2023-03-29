# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from dataclasses import dataclass

import numpy
from scipy.linalg import cho_factor, cho_solve, solve_triangular

from libsigopt.compute.covariance_base import CovarianceBase, DifferentiableCovariance
from libsigopt.compute.misc.constant import (
  CONSTANT_LIAR_MAX,
  CONSTANT_LIAR_MEAN,
  CONSTANT_LIAR_MIN,
  DEFAULT_CONSTANT_LIAR_LIE_NOISE_VARIANCE,
)
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.predictor import Predictor
from libsigopt.compute.python_utils import (
  build_grad_polynomial_tensor,
  build_polynomial_matrix,
  compute_cholesky_for_gp_sampling,
  indices_represent_zero_mean,
  polynomial_index_point_check,
)


# TODO(RTL-38): Think some more on these quantities and the associated enforcement
MINIMUM_KRIGING_VARIANCE = 1e-100  # Just something really small


@dataclass(frozen=True, slots=True)
class PosteriorCoreComponents:
  K_eval: numpy.ndarray
  grad_K_eval: numpy.ndarray
  cardinal_functions_at_points_to_sample: numpy.ndarray


class GaussianProcess(Predictor):
  """To learn more about this stuff, read a book (Rasmussen and Williams or Fasshauer and McCourt)

    Example of mean_poly_indices: [[0,0],[0,1],[1,0],[0,2],[3,4]] would be b_0 + b_1*y + b_2*x + b_3*y^2 + b_4*x^3*y^4

    """

  def __init__(self, covariance, historical_data, mean_poly_indices=None, tikhonov_param=None):
    assert isinstance(covariance, CovarianceBase)
    assert isinstance(historical_data, HistoricalData)
    assert covariance.dim == historical_data.dim
    self.covariance = covariance
    self.historical_data = historical_data
    self.mean_poly_indices = mean_poly_indices
    self._best_index = None
    assert self.num_sampled > 0

    self.tikhonov_param = tikhonov_param

    self.K_chol = None
    self.K_inv_y = None
    self.poly_coef = None
    self.K_inv_demeaned_y = None
    self.demeaned_y = None
    self.K_inv_P = None
    self.PKP_chol = None
    self.P = None

    self.build_precomputed_data()

  @property
  def best_index(self):
    if self._best_index is None:
      self._best_index = numpy.argmin(self.points_sampled_value)
    return self._best_index

  @property
  def best_observed_value(self):
    return self.points_sampled_value[self.best_index]

  @property
  def best_observed_location(self):
    return self.points_sampled[self.best_index, :]

  @property
  def dim(self):
    """Return the number of spatial dimensions."""
    return self.historical_data.dim

  @property
  def num_sampled(self):
    return self.historical_data.num_sampled

  @property
  def differentiable(self):
    return isinstance(self.covariance, DifferentiableCovariance)

  @property
  def has_zero_mean(self):
    """Whether or not the GaussianProcess object has indices indicative of a zero mean."""
    return indices_represent_zero_mean(self.mean_poly_indices)

  @property
  def points_sampled(self):
    return self.historical_data.points_sampled

  @property
  def points_sampled_value(self):
    return self.historical_data.points_sampled_value

  @property
  def points_sampled_noise_variance(self):
    return self.historical_data.points_sampled_noise_variance

  def update_historical_data(self, new_data):
    assert isinstance(new_data, HistoricalData)
    assert new_data.dim == self.dim
    self.historical_data = new_data
    self._best_index = None
    self.build_precomputed_data()

  def get_core_data_copy(self):
    return (
      copy.deepcopy(self.covariance),
      copy.deepcopy(self.historical_data),
      copy.deepcopy(self.mean_poly_indices),
      self.tikhonov_param,
    )

  def build_precomputed_data(self):
    if self.num_sampled == 0:
      self.K_chol = numpy.array([])
      self.K_inv_y = numpy.array([])
    else:
      if self.tikhonov_param is not None:
        noise_diag_vector = numpy.full(self.num_sampled, self.tikhonov_param)
      else:
        noise_diag_vector = self.points_sampled_noise_variance
      kernel_matrix = self.covariance.build_kernel_matrix(
        self.points_sampled,
        noise_variance=noise_diag_vector,
      )
      self.K_chol = cho_factor(kernel_matrix, lower=True, overwrite_a=True)
      self.K_inv_y = cho_solve(self.K_chol, self.points_sampled_value)
    self.fit_nonzero_gp_mean_function()

  def fit_nonzero_gp_mean_function(self):
    r"""Use generalized least squares to fit a nonzero mean function to the data.

        The simplest thing to start with is to just require the mean to be constant, but nonzero.
        Another choice would be just linear, which would require d+1 points before we could talk about anything.

        The nonzero mean is assumed to be mu(x) = p(x)^T*beta where
          beta = inv(P^T*inv(K)*P)*P^T*inv(K)*y
        Each of the rows of P is an evaluation of the polynomial basis in p(x)
        NOTE: The actual computation is slightly different because of the shift on the diagonal.

        TODO(RTL-39): We have come up with an additional consideration in posterior variance

        """
    self.mean_poly_indices = polynomial_index_point_check(self.mean_poly_indices, self.dim)

    if self.has_zero_mean:
      self.poly_coef = numpy.array([0.0])
      self.demeaned_y = numpy.copy(self.points_sampled_value)
      self.K_inv_demeaned_y = self.K_inv_y
    else:
      m = len(self.points_sampled)
      n = len(self.mean_poly_indices)
      if m < n:
        raise ValueError(f"{m} points cannot fit a polynomial with {n} terms because {m}<{n}")

      self.P = build_polynomial_matrix(self.mean_poly_indices, self.points_sampled)
      self.K_inv_P = cho_solve(self.K_chol, self.P)
      PT_K_inv_P = numpy.dot(self.P.T, self.K_inv_P)
      self.PKP_chol = cho_factor(PT_K_inv_P, lower=True, overwrite_a=True)
      self.poly_coef = cho_solve(self.PKP_chol, numpy.dot(self.P.T, self.K_inv_y))
      nonzero_gp_mean = numpy.dot(self.P, self.poly_coef)
      self.demeaned_y = self.points_sampled_value - nonzero_gp_mean
      self.K_inv_demeaned_y = self.K_inv_y - cho_solve(self.K_chol, nonzero_gp_mean)

  def _compute_core_posterior_components(self, points_to_sample, option):
    K_eval = grad_K_eval = cardinal_functions_at_points_to_sample = None
    if option in ("K_eval", "all"):
      K_eval = self.covariance.build_kernel_matrix(self.points_sampled, points_to_sample=points_to_sample)
      if option == "all":
        cardinal_functions_at_points_to_sample = cho_solve(self.K_chol, K_eval.T).T
    if option in ("grad_K_eval", "all"):
      grad_K_eval = self.covariance.build_kernel_grad_tensor(self.points_sampled, points_to_sample=points_to_sample)
    return PosteriorCoreComponents(K_eval, grad_K_eval, cardinal_functions_at_points_to_sample)

  def compute_mean_of_points(self, points_to_sample):
    r"""Compute the mean of this GP at each of point of ``Xs`` (``points_to_sample``).

        For nonzero mean GP, the predictions are s(x) = k(x)^T*inv(K)*(y - P*beta) + p(x)^T*beta.
        Subtract out the mean and add it back in after the zero mean GP is computed

        """
    posterior_core_components = self._compute_core_posterior_components(points_to_sample, "K_eval")
    return self._compute_mean_of_points(points_to_sample, posterior_core_components.K_eval)

  def _compute_mean_of_points(self, points_to_sample, K_eval):
    P_eval = build_polynomial_matrix(self.mean_poly_indices, points_to_sample)
    return numpy.dot(K_eval, self.K_inv_demeaned_y) + numpy.dot(P_eval, self.poly_coef)

  def compute_variance_of_points(self, points_to_sample):
    """Compute the pointwise Kriging variance at a list of points.

        This does not compute the covariance, it only computes
        K(x, x) - k(x)^T * inv(K) * k(x) for a list of values at x.
        It uses K = L * L^T which we have already computed; we call this V = inv(L) * (k(x1) ... k(xm))

        """
    posterior_core_components = self._compute_core_posterior_components(points_to_sample, "K_eval")
    return self._compute_variance_of_points(points_to_sample, posterior_core_components.K_eval)

  def _compute_variance_of_points(self, points_to_sample, K_eval, cardinal_functions_at_points_to_sample=None):
    K_x_x_array = self.covariance.covariance(points_to_sample, points_to_sample)
    if cardinal_functions_at_points_to_sample is None:
      V = solve_triangular(
        self.K_chol[0],
        K_eval.T,
        lower=self.K_chol[1],
        overwrite_b=True,
      )
      schur_complement_component = numpy.sum(V**2, axis=0)
    else:
      schur_complement_component = numpy.sum(K_eval * cardinal_functions_at_points_to_sample, axis=1)
    return numpy.fmax(MINIMUM_KRIGING_VARIANCE, K_x_x_array - schur_complement_component)

  def compute_mean_and_variance_of_points(self, points_to_sample):
    posterior_core_components = self._compute_core_posterior_components(points_to_sample, "K_eval")
    mean = self._compute_mean_of_points(points_to_sample, posterior_core_components.K_eval)
    var = self._compute_variance_of_points(points_to_sample, posterior_core_components.K_eval)
    return mean, var

  def compute_grad_mean_of_points(self, points_to_sample):
    r"""Compute the gradient of the mean of this GP at each of point of ``Xs`` (``points_to_sample``) wrt ``Xs``."""
    posterior_core_components = self._compute_core_posterior_components(points_to_sample, "grad_K_eval")
    return self._compute_grad_mean_of_points(points_to_sample, posterior_core_components.grad_K_eval)

  def _compute_grad_mean_of_points(self, points_to_sample, grad_K_eval):
    grad_P_eval = build_grad_polynomial_tensor(self.mean_poly_indices, points=points_to_sample)
    return (
      numpy.einsum("ijk, j", grad_K_eval, self.K_inv_demeaned_y)
      + numpy.einsum("ijk, j", grad_P_eval, self.poly_coef)
    )

  # NOTE: An aspect of computation required in compute_variance is copied here for efficiency.
  #       Also, technically, some of the covariance computation is being repeated unnecessarily.
  def compute_grad_variance_of_points(self, points_to_sample):
    posterior_core_components = self._compute_core_posterior_components(points_to_sample, "all")
    return self._compute_grad_variance_of_points(
      posterior_core_components.grad_K_eval,
      posterior_core_components.cardinal_functions_at_points_to_sample,
    )

  def _compute_grad_variance_of_points(self, grad_K_eval, cardinal_functions_at_points_to_sample):
    if not self.covariance.translation_invariant:
      raise NotImplementedError("Not yet ready for general kernels.")

    return -2 * numpy.sum(grad_K_eval * cardinal_functions_at_points_to_sample[:, :, None], axis=1)

  def compute_mean_variance_grad_of_points(self, points_to_sample):
    pcc = self._compute_core_posterior_components(points_to_sample, "all")

    mean = self._compute_mean_of_points(points_to_sample, pcc.K_eval)
    var = self._compute_variance_of_points(points_to_sample, pcc.K_eval, pcc.cardinal_functions_at_points_to_sample)
    grad_mean = self._compute_grad_mean_of_points(points_to_sample, pcc.grad_K_eval)
    grad_var = self._compute_grad_variance_of_points(pcc.grad_K_eval, pcc.cardinal_functions_at_points_to_sample)

    return mean, var, grad_mean, grad_var

  def compute_covariance_of_points(self, points_to_sample):
    r"""Compute the variance (matrix) of this GP at each point of ``Xs`` (``points_to_sample``).

        .. Warning:: ``points_to_sample`` should not contain duplicate points.

        The variance matrix is symmetric although we currently return the full representation.

        """
    K_eval_var = self.covariance.build_kernel_matrix(points_to_sample)
    if self.num_sampled == 0:
      return numpy.diag(numpy.diag(K_eval_var))

    K_eval = self.covariance.build_kernel_matrix(self.points_sampled, points_to_sample=points_to_sample)
    V = solve_triangular(
      self.K_chol[0],
      K_eval.T,
      lower=self.K_chol[1],
      overwrite_b=True,
    )

    return K_eval_var - numpy.dot(V.T, V)

  def draw_posterior_samples_of_points(self, num_samples, points_to_sample):
    r"""Draw samples from the posterior at ``Xs`` (``point_to_sample``)) points.

        To draw samples we use the formula s(Xs) + (L * Z)^T, where K(Xs) = L * L^T is the covariance of ``Xs``
        and Z are samples drawn from a normal distribution.

        """
    mean = self.compute_mean_of_points(points_to_sample)
    cov = self.compute_covariance_of_points(points_to_sample)
    L = compute_cholesky_for_gp_sampling(cov)

    # z_samples is an array with shape (num_points, num_samples)
    z_samples = numpy.atleast_2d(numpy.random.normal(size=(len(mean), num_samples)))
    return mean[None, :] + numpy.transpose(numpy.dot(L, z_samples))

  def draw_posterior_samples(self, num_samples):
    return self.draw_posterior_samples_of_points(num_samples, self.points_sampled)

  def append_lie_data(self, lie_locations, lie_method=CONSTANT_LIAR_MIN):
    assert lie_method in (CONSTANT_LIAR_MAX, CONSTANT_LIAR_MIN, CONSTANT_LIAR_MEAN)
    if lie_method == CONSTANT_LIAR_MIN:
      lie_value = numpy.max(self.historical_data.points_sampled_value)
    elif lie_method == CONSTANT_LIAR_MAX:
      lie_value = numpy.min(self.historical_data.points_sampled_value)
    else:
      lie_value = numpy.mean(self.historical_data.points_sampled_value)

    self.historical_data.append_historical_data(
      lie_locations,
      lie_value * numpy.ones(len(lie_locations)),
      DEFAULT_CONSTANT_LIAR_LIE_NOISE_VARIANCE * numpy.ones(len(lie_locations)),
    )
    self.update_historical_data(self.historical_data)
