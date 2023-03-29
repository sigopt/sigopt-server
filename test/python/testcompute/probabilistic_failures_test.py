# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Test the Python implementation of Knowledge Gradient."""

import numpy
from scipy.stats import norm

from libsigopt.compute.probabilistic_failures import (
  POSITIVE_EXPONENT_CAP,
  ProbabilisticFailures,
  ProbabilisticFailuresCDF,
  ProductOfListOfProbabilisticFailures,
)
from testcompute.gaussian_process_test_case import GaussianProcessTestCase


class TestProbabilisticFailures(GaussianProcessTestCase):
  def test_probability_value_bounded(self, one_hot_domain_list, gaussian_process_list):
    for domain, gp in zip(one_hot_domain_list, gaussian_process_list):
      threshold = numpy.random.randn() * 0.05
      pf = ProbabilisticFailures(gp, threshold)
      pfcdf = ProbabilisticFailuresCDF(gp, threshold)

      num_to_evaluate = 10
      points_to_evaluate = domain.generate_quasi_random_points_in_domain(num_to_evaluate)
      probability_values = pf.compute_probability_of_success(points_to_evaluate)
      assert (numpy.array(probability_values) >= 0).all() and (numpy.array(probability_values) <= 1).all()

      probability_values = pfcdf.compute_probability_of_success(points_to_evaluate)
      assert (numpy.array(probability_values) >= 0).all() and (numpy.array(probability_values) <= 1).all()

  def test_probability_values(self, one_hot_domain_list, gaussian_process_list):
    for domain, gp in zip(one_hot_domain_list, gaussian_process_list):
      threshold = numpy.random.randn() * 0.05
      pf = ProbabilisticFailures(gp, threshold)
      pfcdf = ProbabilisticFailuresCDF(gp, threshold)

      num_to_evaluate = 10
      points_to_evaluate = domain.generate_quasi_random_points_in_domain(num_to_evaluate)
      probability_values = pf.compute_probability_of_success(points_to_evaluate)

      means = pf.predictor.compute_mean_of_points(points_to_evaluate)
      exponent = pf.kappa * (means - threshold)
      exponent[exponent > POSITIVE_EXPONENT_CAP] = POSITIVE_EXPONENT_CAP
      prob_of_success = 1.0 / (1.0 + numpy.exp(exponent))

      for p, q in zip(probability_values, prob_of_success):
        self.assert_scalar_within_relative(p, q, 1.0e-14)

      probability_values = pfcdf.compute_probability_of_success(points_to_evaluate)
      means = pfcdf.predictor.compute_mean_of_points(points_to_evaluate)
      variances = pfcdf.predictor.compute_variance_of_points(points_to_evaluate)
      prob_of_success = norm.cdf((threshold - means) / numpy.sqrt(variances))

      for p, q in zip(probability_values, prob_of_success):
        self.assert_scalar_within_relative(p, q, 1.0e-14)

  def test_grad_probability_values(self, one_hot_domain_list, gaussian_process_list):
    for domain, gp in zip(one_hot_domain_list, gaussian_process_list):
      threshold = numpy.random.randn() * 0.05
      pf = ProbabilisticFailures(gp, threshold)

      num_to_evaluate = 10
      points_to_evaluate = domain.generate_quasi_random_points_in_domain(num_to_evaluate)
      grad_probability_from_pf = pf.compute_grad_probability_of_success(points_to_evaluate)

      means = pf.predictor.compute_mean_of_points(points_to_evaluate)
      exponent = pf.kappa * (means - threshold)
      exponent[exponent > POSITIVE_EXPONENT_CAP] = POSITIVE_EXPONENT_CAP
      grad_logistic = pf.kappa * numpy.exp(exponent) / (1.0 + numpy.exp(exponent)) ** 2

      grad_prob_of_success = -grad_logistic[:, None] * pf.predictor.compute_grad_mean_of_points(points_to_evaluate)

      for grad_p_from_pf, grad_p in zip(grad_probability_from_pf, grad_prob_of_success):
        self.assert_vector_within_relative(grad_p_from_pf, grad_p, 1.0e-14)

  def test_grad_against_finite_difference(self, one_hot_domain_list, gaussian_process_list):
    h = 1e-7
    n_test = 50
    for domain, gp in zip(one_hot_domain_list, gaussian_process_list):
      threshold = numpy.random.randn() * 0.05
      pf = ProbabilisticFailuresCDF(gp, threshold)
      pts = domain.generate_quasi_random_points_in_domain(n_test)
      self.check_gradient_with_finite_difference(
        pts,
        pf.compute_probability_of_success,
        pf.compute_grad_probability_of_success,
        tol=domain.dim * 1e-6,
        fd_step=h * numpy.ones(domain.dim),
        use_complex=True,
      )


class TestProductOfListOfProbabilisticFailures(GaussianProcessTestCase):
  def test_probability_values(self, one_hot_domain_list, list_probabilistic_failures_list):
    for domain, list_of_pfs in zip(one_hot_domain_list, list_probabilistic_failures_list):
      ppf = ProductOfListOfProbabilisticFailures(list_of_pfs)
      points_to_evaluate = domain.generate_quasi_random_points_in_domain(100)
      product_pv = ppf.compute_probability_of_success(points_to_evaluate)
      product = 1
      for pf in list_of_pfs:
        product *= pf.compute_probability_of_success(points_to_evaluate)
      self.assert_vector_within_relative(product_pv, product, 1.0e-15)
      assert numpy.all((product_pv >= 0) * (product_pv <= 1))
