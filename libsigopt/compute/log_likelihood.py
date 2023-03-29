# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import scipy.linalg

from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.optimization import ScipyOptimizable


DEFAULT_LOG_LIKELIHOOD_SCALING_FACTOR = 1.0
DEFAULT_TIKHONOV_PARAMETER = 1.0e-10
INCLUDE_NONZERO_MEAN_GRADIENT_CORRECTION = False


# customlint: disable=AccidentalFormatStringRule
class GaussianProcessLogMarginalLikelihood(ScipyOptimizable):
  r"""

    AUTO_NOISE
    If you are attempting to allow for this to automatically solve for the Tikhonov regularization parameter mu,
    you must activate use_auto_noise.  The hyperparameters with use_auto_noise == True are:
      hyperparameters = [alpha, l_1, ..., l_d, mu]
    If you try to pass the wrong hyperparameter structure in, this will error.

    """

  def __init__(
    self,
    covariance,
    historical_data,
    mean_poly_indices=None,
    use_auto_noise=False,
    log_domain=False,
    scaling_factor=DEFAULT_LOG_LIKELIHOOD_SCALING_FACTOR,
  ):
    """Construct a LogLikelihood object for selecting hyperparameters.

        log_domain=True can be useful for the model selection process because conducting the search for parameters
        in the log domain is probably more natural.  But may not make a difference.

        scaling_factor just scales all values returned from this by that value.  Sometimes setting this small can help
        convergence for derivative based methods.

        """
    super().__init__()
    self.gp = GaussianProcess(
      covariance,
      historical_data,
      mean_poly_indices=mean_poly_indices,
      tikhonov_param=DEFAULT_TIKHONOV_PARAMETER if use_auto_noise else None,
    )
    self.covariance = covariance
    self.historical_data = historical_data
    self.mean_poly_indices = mean_poly_indices
    self.use_auto_noise = use_auto_noise
    self.log_domain = log_domain
    if scaling_factor <= 0:
      raise ValueError(f"Non-positive scaling factor = {scaling_factor}")
    self.scaling_factor = scaling_factor

  """
  Return the number of hyperparameters we are actually solving for.

  To clarify the difference between dim, problem_size, and num_hyperparameters:
  dim refers to the dimensionality of the physical problem - i.e. if the experiment has 2 parameters => dim = 2.
  num_hyperparameters refers to the number of hyperparameters passed in. The hyperparmeters has the form of:
    hyperparameters = [alpha, l_1, ..., l_d, mu], where mu is optinal.
  problem_size refers to the number of hyperparameters we are actually trying to optimize. For example,
    the problem_size for a LogProfileLikelihood for an experiment with two parameters and AUTO_NOISE
    would be 4 - 1 = 3 since we do not need to optimize for alpha.
  """
  @property
  def num_hyperparameters(self):
    return self.covariance.num_hyperparameters + (1 if self.use_auto_noise else 0)

  @property
  def differentiable(self):
    return self.gp.differentiable

  @property
  def problem_size(self):
    return self.num_hyperparameters

  @property
  def tikhonov_param(self):
    return self.gp.tikhonov_param

  def get_hyperparameters(self):
    if self.use_auto_noise:
      hyperparameters = numpy.append(self.covariance.hyperparameters, self.tikhonov_param)
    else:
      hyperparameters = self.covariance.hyperparameters
    return numpy.log(hyperparameters) if self.log_domain else hyperparameters

  def set_hyperparameters(self, hyperparameters):
    if len(hyperparameters) != self.problem_size:
      extra_advice = " Remember to include 1 extra hyperparameter for auto_noise." if self.use_auto_noise else ""
      raise ValueError(f"Expected {self.problem_size} hyperparameters, received {len(hyperparameters)}.{extra_advice}")
    hp_linear_domain = numpy.exp(hyperparameters) if self.log_domain else hyperparameters
    # Don't pass the noise term in covariance.hyperparameters since we pass it as a separate param
    self.covariance.hyperparameters = hp_linear_domain[: self.gp.dim + 1]
    tikhonov_param = hp_linear_domain[-1] if self.use_auto_noise else None
    self.gp = GaussianProcess(self.covariance, self.historical_data, self.mean_poly_indices, tikhonov_param)

  hyperparameters = property(get_hyperparameters, set_hyperparameters)
  current_point = hyperparameters

  def compute_log_likelihood(self):
    r"""Compute the log marginal likelihood at the specified hyperparameters.

        L(theta) = y^T*inv(K)*y + log(det(K))

        Because our optimization tool maximizes things, but we want to minimize this, we return the negative.

        """

    y_Pb = self.gp.demeaned_y
    Kinvy_Pb = self.gp.K_inv_demeaned_y
    L = self.gp.K_chol[0]
    log_likelihood = numpy.dot(y_Pb, Kinvy_Pb) + 2 * numpy.sum(numpy.log(L.diagonal()))
    return -self.scaling_factor * log_likelihood

  compute_objective_function = compute_log_likelihood

  def compute_grad_log_likelihood(self, include_nonzero_correction=INCLUDE_NONZERO_MEAN_GRADIENT_CORRECTION):
    r"""
        Compute the gradient (wrt hyperparameters) of the _log_likelihood_type measure at the specified hyperparameters.

        Computes
        ``\pderiv{log(p(y | X, \theta))}{\theta_k} = \frac{1}{2} * y_i * \pderiv{K_{ij}}{\theta_k} * y_j - \frac{1}{2}``
        ``* trace(K^{-1}_{ij}\pderiv{K_{ij}}{\theta_k})``
        Or equivalently, ``= \frac{1}{2} * trace([\alpha_i \alpha_j - K^{-1}_{ij}]*\pderiv{K_{ij}}{\theta_k})``, where
        ``\alpha_i = K^{-1}_{ij} * y_j``

        The log_scaling accounts for d/da L(exp(a)) = L'(exp(a)) * exp(a).

        """
    grad_hyperparameter_cov_tensor = self.covariance.build_kernel_hparam_grad_tensor(self.gp.points_sampled)
    if self.use_auto_noise:
      grad_hyperparameter_cov_tensor = numpy.concatenate(
        (grad_hyperparameter_cov_tensor, numpy.eye(self.gp.num_sampled)[:, :, None]),
        axis=2,
      )
    grad_log_marginal = numpy.empty(self.num_hyperparameters)
    Kinvy_Pb = self.gp.K_inv_demeaned_y
    K_chol = self.gp.K_chol
    for k in range(self.problem_size):
      # TODO(RTL-55): Maybe this can be reorganized using blas level stuff
      dK = grad_hyperparameter_cov_tensor[:, :, k]
      dKKinvy_Pb = numpy.dot(dK, Kinvy_Pb)
      grad_log_marginal[k] = -numpy.dot(Kinvy_Pb, dKKinvy_Pb)
      grad_log_marginal[k] += numpy.trace(scipy.linalg.cho_solve(K_chol, dK, overwrite_b=True))
      if not self.gp.has_zero_mean and include_nonzero_correction:
        P = self.gp.P
        KinvP = self.gp.K_inv_P
        PKP_chol = self.gp.PKP_chol
        temp = -numpy.dot(P, scipy.linalg.cho_solve(PKP_chol, numpy.dot(KinvP.T, numpy.dot(dK, Kinvy_Pb))))
        grad_log_marginal[k] += 2 * numpy.dot(Kinvy_Pb, temp)

    log_scaling = numpy.exp(self.hyperparameters) if self.log_domain else 1.0

    return -self.scaling_factor * grad_log_marginal * log_scaling

  compute_grad_objective_function = compute_grad_log_likelihood
