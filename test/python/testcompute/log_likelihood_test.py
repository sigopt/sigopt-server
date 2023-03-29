# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Test cases for the Log Marginal Likelihood metric for model fit."""
import numpy
import pytest
import scipy

from libsigopt.compute.covariance import C2RadialMatern, C4RadialMatern, SquareExponential
from libsigopt.compute.domain import ContinuousDomain
from libsigopt.compute.log_likelihood import GaussianProcessLogMarginalLikelihood
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.optimization import MultistartOptimizer, SLSQPOptimizer
from libsigopt.compute.optimization_auxiliary import DEFAULT_SLSQP_PARAMETERS
from testcompute.gaussian_process_test_case import GaussianProcessTestCase


def evaluate_log_likelihood_at_hyperparameter_list(log_likelihood_evaluator, hyperparameters_to_evaluate):
  """Compute the specified log likelihood measure at each input set of hyperparameters.

    Will return 'nan' if the specified hyperparameters create a singular matrix.

    """

  current_hparams = log_likelihood_evaluator.hyperparameters

  values = []
  for hparams in hyperparameters_to_evaluate:
    try:
      log_likelihood_evaluator.hyperparameters = hparams
    except numpy.linalg.LinAlgError:
      values.append(float("nan"))
    except ValueError as e:
      raise ValueError(
        f"The hparams {hparams} are inappropriate for covariance {log_likelihood_evaluator.covariance}"
      ) from e
    else:
      values.append(log_likelihood_evaluator.compute_log_likelihood())

  log_likelihood_evaluator.hyperparameters = current_hparams

  return values


class TestGaussianProcessLogMarginalLikelihood(GaussianProcessTestCase):
  """Test cases for the Log Marginal Likelihood metric for model fit."""

  @pytest.fixture
  def dim(self):
    return 3

  @pytest.fixture
  def hyperparameter_domain(self, dim):
    num_hyperparameters = dim + 1
    domain_bounds = [[3.0, 5.0]] * num_hyperparameters
    return ContinuousDomain(domain_bounds)

  @pytest.fixture
  def num_sampled_list(self):
    return [1, 2, 5, 10, 16, 20, 42]

  def test_grad_log_likelihood_pings(self, dim, num_sampled_list):
    """Ping test (compare analytic result to finite difference) the log likelihood gradient wrt hyperparameters."""
    numpy.random.seed(2014)
    h = 2.0e-4
    tolerance = 5.0e-6

    for num_sampled in num_sampled_list:
      gaussian_process = self.form_deterministic_gaussian_process(dim, num_sampled)
      python_cov, historical_data, mean_poly_indices, _ = gaussian_process.get_core_data_copy()

      lml = GaussianProcessLogMarginalLikelihood(python_cov, historical_data, mean_poly_indices)

      def func(hparams):
        lml.hyperparameters = hparams.squeeze()
        return lml.compute_log_likelihood()

      def grad(hparams):
        lml.hyperparameters = hparams.squeeze()
        return lml.compute_grad_log_likelihood()

      hparams = lml.hyperparameters.copy()
      self.check_gradient_with_finite_difference(
        numpy.reshape(hparams, (1, -1)),
        func,
        grad,
        tol=tolerance,
        fd_step=h * numpy.ones(lml.num_hyperparameters),
      )

  @pytest.mark.parametrize("kernel", [SquareExponential, C2RadialMatern, C4RadialMatern])
  @pytest.mark.parametrize("log_domain", [False, True])
  @pytest.mark.parametrize("dim", range(1, 5))
  def test_grad_log_likelihood(self, kernel, log_domain, dim):
    numpy.random.seed(0)

    # Due to some numerical issues it's best to stick to powers of two here that are close to the square root of machine
    # epsilon. Using other values produces wild results.
    eps = 2**-10

    num_points = dim * 10

    # Sample historical_data
    hd = HistoricalData(dim=dim)
    hd.append_historical_data(
      points_sampled=numpy.random.rand(num_points, dim),
      points_sampled_value=numpy.random.rand(num_points),
      points_sampled_noise_variance=0.1 * numpy.abs(numpy.random.rand(num_points)),
    )

    # Construct hyperparameter domain
    if log_domain:
      hdomain = ContinuousDomain(
        [[numpy.log(1e-6), numpy.log(1e3)]] + [[numpy.log(2 * 0.001), numpy.log(2 * 10)]] * dim
      )
    else:
      hdomain = ContinuousDomain([[1e-6, 1e3]] + [[2 * 0.001, 2 * 10]] * dim)

    def ll(params):
      return GaussianProcessLogMarginalLikelihood(
        covariance=kernel(numpy.exp(params) if log_domain else params),
        historical_data=hd,
        log_domain=log_domain,
      ).compute_log_likelihood()

    for pt in hdomain.generate_quasi_random_points_in_domain(100):
      grad = GaussianProcessLogMarginalLikelihood(
        covariance=kernel(numpy.exp(pt) if log_domain else pt),
        historical_data=hd,
        log_domain=log_domain,
      ).compute_grad_log_likelihood()

      approx_grad = scipy.optimize.approx_fprime(pt, ll, eps)

      grad_norm = numpy.linalg.norm(grad)
      approx_grad_norm = numpy.linalg.norm(approx_grad)
      grad_normed = grad / grad_norm
      approx_grad_normed = approx_grad / approx_grad_norm

      # It turns out that the scale can be a bit off when doing this numerical approximation, but what we really
      # care about is the direction anyway since most methods will end up doing line search.
      assert numpy.abs(numpy.dot(grad_normed, approx_grad_normed) - 1) <= 1e-3

  def test_evaluate_log_likelihood_at_points(self, deterministic_gaussian_process, hyperparameter_domain):
    """Check that ``evaluate_log_likelihood_at_hyperparameter_list`` computes and orders results correctly."""
    gaussian_process = deterministic_gaussian_process
    python_cov, historical_data, mean_poly_indices, _ = gaussian_process.get_core_data_copy()

    lml = GaussianProcessLogMarginalLikelihood(python_cov, historical_data, mean_poly_indices)

    num_to_eval = 10
    domain = hyperparameter_domain
    hyperparameters_to_evaluate = domain.generate_quasi_random_points_in_domain(num_to_eval)

    test_values = evaluate_log_likelihood_at_hyperparameter_list(lml, hyperparameters_to_evaluate)

    for i, value in enumerate(test_values):
      lml.hyperparameters = hyperparameters_to_evaluate[i, ...]
      truth = lml.compute_log_likelihood()
      assert value == truth

  def test_multistarted_hyperparameter_optimization(self, deterministic_gaussian_process, hyperparameter_domain):
    """Check that multistarted optimization can find the optimum hyperparameters."""
    random_state = numpy.random.get_state()
    numpy.random.seed(87612)

    tolerance = 1.0e-3
    num_multistarts = 30

    gaussian_process = deterministic_gaussian_process
    python_cov, historical_data, mean_poly_indices, _ = gaussian_process.get_core_data_copy()

    lml = GaussianProcessLogMarginalLikelihood(python_cov, historical_data, mean_poly_indices)

    num_hyperparameters = hyperparameter_domain.dim
    domain = ContinuousDomain([[0.01, 10]] * num_hyperparameters)

    log_likelihood_optimizer = SLSQPOptimizer(domain, lml, DEFAULT_SLSQP_PARAMETERS)
    multistart_optimizer = MultistartOptimizer(
      log_likelihood_optimizer,
      num_multistarts=num_multistarts,
      log_sample=True,
    )
    best_hyperparameters, _ = multistart_optimizer.optimize()

    # Check that gradients are small
    lml.hyperparameters = best_hyperparameters
    gradient = lml.compute_grad_log_likelihood()
    if not domain.check_point_on_boundary(best_hyperparameters, 1e-4):
      self.assert_vector_within_relative_norm(gradient, numpy.zeros(self.num_hyperparameters), tolerance)

    # Check that output is in the domain
    assert domain.check_point_acceptable(best_hyperparameters) is True

    numpy.random.set_state(random_state)
