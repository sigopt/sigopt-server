# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME
from libsigopt.compute.covariance import SquareExponential
from libsigopt.compute.domain import CategoricalDomain, ContinuousDomain
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData, SingleMetricMidpointInfo
from libsigopt.compute.probabilistic_failures import (
  ProbabilisticFailures,
  ProbabilisticFailuresCDF,
  ProductOfListOfProbabilisticFailures,
)
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import form_points_sampled, form_random_hyperparameter_dict


def fill_random_covariance_hyperparameters(interval, num_hyperparameters, covariance_type):
  assert len(interval) == 2
  return covariance_type([numpy.random.uniform(*interval) for _ in range(num_hyperparameters)])


def fill_random_domain_bounds(lower_bound_interval, upper_bound_interval, dim):
  assert len(lower_bound_interval) == len(upper_bound_interval) == 2
  domain_bounds = numpy.empty((dim, 2))
  domain_bounds[:, 0] = numpy.random.uniform(*lower_bound_interval)
  domain_bounds[:, 1] = numpy.random.uniform(*upper_bound_interval)
  return domain_bounds


GP_FIXTURE_SCOPE = "module"


class GaussianProcessTestCase(NumericalTestCase):
  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def domain_list(self):
    dim_list = [1, 3, 5, 9]
    return [self.form_continous_and_uniform_domain(dim=dim, lower_element=-1, higher_element=1) for dim in dim_list]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def one_hot_domain_list(self, domain_list):
    return [domain.one_hot_domain for domain in domain_list]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def any_domain_list(self):
    random_dim_list = sorted(numpy.random.choice(range(2, 25), 10, replace=False))
    return [
      self.form_continous_and_uniform_domain(dim=dim, lower_element=-1, higher_element=1) for dim in random_dim_list
    ]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def any_one_hot_domain_list(self, any_domain_list):
    return [domain.one_hot_domain for domain in any_domain_list]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def gaussian_process_list(self, domain_list):
    num_sampled = [4, 8, 15, 16]
    return [
      self.form_gaussian_process_and_data(domain, num_sampled=num_sampled)
      for domain, num_sampled in zip(domain_list, num_sampled)
    ]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def any_gaussian_process_list(self, any_domain_list):
    return [self.form_gaussian_process_and_data(domain, num_sampled) for num_sampled, domain in zip(any_domain_list)]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def gaussian_process_and_domain(self):
    dim = numpy.random.randint(1, 9)
    domain = self.form_continous_and_uniform_domain(dim)
    gaussian_process = self.form_gaussian_process_and_data(domain)
    return gaussian_process, domain

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def deterministic_gaussian_process(self):
    return self.form_deterministic_gaussian_process(dim=3, num_sampled=10)

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def probabilistic_failures_list(self, gaussian_process_list):
    pf_list = []
    for gp in gaussian_process_list:
      cov, data, mpi, tikhonov = gp.get_core_data_copy()
      data.points_sampled_values = numpy.sum((data.points_sampled - 0.2) ** 2, axis=1)
      threshold = numpy.random.uniform(0.2, 0.8)
      pf = ProbabilisticFailures(GaussianProcess(cov, data, mpi, tikhonov), threshold)
      pf_list.append(pf)
    return pf_list

  @pytest.fixture(scope=GP_FIXTURE_SCOPE, params=[True, False])
  def list_probabilistic_failures_list(self, request, domain_list):
    num_gps_list = [1, 2, 4, 8]
    num_sampled_list = [8, 14, 26, 48]
    return [
      self.form_list_of_probabilistic_failures(num_gp, domain, num_sampled, pf_cdf=request.param)
      for domain, num_sampled, num_gp in zip(domain_list, num_gps_list, num_sampled_list)
    ]

  @pytest.fixture(scope=GP_FIXTURE_SCOPE)
  def product_of_list_probabilistic_failures_list(self, list_probabilistic_failures_list):
    return [ProductOfListOfProbabilisticFailures(list_of_pfs) for list_of_pfs in list_probabilistic_failures_list]

  @staticmethod
  def form_continous_and_uniform_domain(dim=3, lower_element=-2, higher_element=2):
    return CategoricalDomain(
      [{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [lower_element, higher_element]}] * dim
    )

  @staticmethod
  def form_list_of_probabilistic_failures(num_gps, domain, num_sampled, noise_per_point=1e-2, pf_cdf=True):
    list_of_pfs = []
    for _ in range(num_gps):
      gp = GaussianProcessTestCase.form_gaussian_process_and_data(
        domain,
        num_sampled=num_sampled,
        noise_per_point=noise_per_point,
      )
      threshold = numpy.random.random() * (numpy.max(gp.points_sampled_value) - numpy.min(gp.points_sampled_value))
      pf_class = ProbabilisticFailuresCDF if pf_cdf else ProbabilisticFailures
      list_of_pfs.append(pf_class(gp, threshold))
    return list_of_pfs

  @staticmethod
  def form_gaussian_process_and_data(domain, mpi=None, num_sampled=50, noise_per_point=0.002):
    if mpi is None:
      mpi = [[0] * domain.one_hot_dim] if num_sampled > 2 else [[]]
    hparam_dict = form_random_hyperparameter_dict(domain)[0]
    length_scales = numpy.concatenate(hparam_dict["length_scales"]).tolist()
    cov = SquareExponential([hparam_dict["alpha"]] + length_scales)
    points_sampled = form_points_sampled(
      domain.one_hot_domain,
      num_sampled,
      noise_per_point,
      num_metrics=1,
      task_options=numpy.array([]),
      snap_cats=True,
      failure_prob=0,
    )
    return GaussianProcessTestCase.form_gaussian_process(
      points_sampled.points,
      cov,
      mpi,
      points_sampled.value_vars[:, 0],
    )

  @staticmethod
  def form_deterministic_gaussian_process(dim, num_sampled, noise_variance_base=0.002):
    # HACK: This is one seed for which the tests I care about pass.  We'll need to think some more
    #  about exactly what we ought to be testing, though.
    numpy.random.seed(14)
    num_hyperparameters = dim + 1
    covariance = fill_random_covariance_hyperparameters(
      interval=(3.0, 5.0),
      num_hyperparameters=num_hyperparameters,
      covariance_type=SquareExponential,
    )
    domain_bounds = fill_random_domain_bounds(
      dim=dim,
      lower_bound_interval=(-2.0, 0.5),
      upper_bound_interval=(2.0, 3.5),
    )
    domain = ContinuousDomain(domain_bounds)
    points_sampled = domain.generate_quasi_random_points_in_domain(num_sampled)
    gaussian_process = GaussianProcessTestCase.form_gaussian_process(
      points_sampled,
      covariance,
      noise_variance=numpy.full(num_sampled, noise_variance_base),
    )
    return gaussian_process

  @staticmethod
  def form_gaussian_process(
    points_sampled,
    covariance,
    mean_poly_indices=None,
    noise_variance=None,
    tikhonov_param=None,
  ):
    num_points, dim = points_sampled.shape

    mean = numpy.mean(points_sampled, axis=0)
    values = numpy.exp(-numpy.sum((points_sampled - mean[None, :]) ** 2, axis=1))
    noise_variance = numpy.zeros(num_points) if noise_variance is None else noise_variance
    mmi = SingleMetricMidpointInfo(values, numpy.zeros_like(values))
    scaled_values = mmi.relative_objective_value(values)
    scaled_variance = mmi.relative_objective_variance(noise_variance)

    historical_data = HistoricalData(dim)
    historical_data.append_historical_data(points_sampled, scaled_values, scaled_variance)

    mean_poly_indices = [[]] if mean_poly_indices is None else mean_poly_indices
    return GaussianProcess(covariance, historical_data, mean_poly_indices, tikhonov_param=tikhonov_param)
