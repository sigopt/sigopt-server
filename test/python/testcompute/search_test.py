# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.aux.geometry_utils import compute_distance_matrix_squared
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.probabilistic_failures import ProbabilisticFailuresCDF
from libsigopt.compute.search import (
  ProbabilityOfImprovementSearch,
  convert_one_hot_to_search_hypercube_points,
  map_non_categorical_points_from_unit_hypercube,
  map_non_categorical_points_to_unit_hypercube,
  round_one_hot_points_categorical_values_to_target,
)
from testcompute.gaussian_process_test_case import GaussianProcessTestCase
from testcompute.zigopt_input_utils import form_random_unconstrained_categorical_domain


class TestSearch(GaussianProcessTestCase):
  def test_pi_search_grad_fail(self, domain_list, product_of_list_probabilistic_failures_list):
    for domain, prod_of_pfs in zip(domain_list, product_of_list_probabilistic_failures_list):
      random_distance = numpy.random.random()
      pi_search = ProbabilityOfImprovementSearch(domain, prod_of_pfs, random_distance)

      random_distance = numpy.random.random()
      pi_search = ProbabilityOfImprovementSearch(domain, prod_of_pfs, random_distance)
      points_to_evaluate = domain.one_hot_domain.generate_quasi_random_points_in_domain(100)
      with pytest.raises(AssertionError):
        pi_search.evaluate_grad_at_point_list(points_to_evaluate)

  def test_pi_search_no_repulsor(self, domain_list, product_of_list_probabilistic_failures_list):
    for domain, prod_of_pfs in zip(domain_list, product_of_list_probabilistic_failures_list):
      random_distance = numpy.random.random()
      pi_search = ProbabilityOfImprovementSearch(domain, prod_of_pfs, random_distance)

      points_to_evaluate = domain.one_hot_domain.generate_quasi_random_points_in_domain(100)
      product_pv = prod_of_pfs.compute_probability_of_success(points_to_evaluate)
      pi = pi_search.evaluate_at_point_list(points_to_evaluate)
      self.assert_vector_within_relative_norm(pi, product_pv, 1e-15)
      assert numpy.all((pi >= 0) * (pi <= 1))

  def test_pi_search_with_repulsor_points(self, domain_list, product_of_list_probabilistic_failures_list):
    for domain, prod_of_pfs in zip(domain_list, product_of_list_probabilistic_failures_list):
      random_distance = numpy.random.random()
      gp_points = numpy.copy(prod_of_pfs.list_of_probabilistic_failures[0].predictor.points_sampled)
      pi_search = ProbabilityOfImprovementSearch(domain, prod_of_pfs, random_distance, gp_points)
      points_to_evaluate = domain.one_hot_domain.generate_quasi_random_points_in_domain(100)
      pi = pi_search.evaluate_at_point_list(points_to_evaluate)
      assert numpy.all((pi >= 0) * (pi <= 1))

      pi_search.add_normalized_repulsor_point(points_to_evaluate)
      pi = pi_search.evaluate_at_point_list(points_to_evaluate)
      assert numpy.all(pi == 0)

  def test_pi_search_with_evaluate_at_point_lists(self):
    first_cat_elements = [1, 3, 5]
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": first_cat_elements},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5, 5]},
      ]
    )
    gp = self.form_gaussian_process_and_data(
      domain=domain,
      mpi=None,
      num_sampled=10,
      noise_per_point=1e-5,
    )
    threshold = 0.5 * (numpy.max(gp.points_sampled_value) - numpy.min(gp.points_sampled_value))
    pf = ProbabilisticFailuresCDF(gp, threshold)
    distance = 0.25
    pi_search = ProbabilityOfImprovementSearch(domain, pf, distance)
    pi_search.add_normalized_repulsor_point(numpy.array([[0, 1, 0, 0, 0]]))
    points_to_evaluate = numpy.array(
      [
        [0, 1, 0, 0, 3.6],
        [0, 1, 0, 0, -4.9],
        [4, 1, 0, 0, 3],
        [2, 1, 0, 0, 4.5],
      ]
    )
    pi = pi_search.evaluate_at_point_list(points_to_evaluate)
    assert numpy.all(pi == 0)

    points_to_evaluate = numpy.array(
      [
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [7, 1, 0, 0, 0],
        [10, 1, 0, 0, -1.5],
        [5, 1, 0, 0, 3],
        [3, 1, 0, 0, 4.5],
      ]
    )
    pi = pi_search.evaluate_at_point_list(points_to_evaluate)
    pos = pf.compute_probability_of_success(points_to_evaluate)
    self.assert_vector_within_relative_norm(pi, pos, 1e-15)

  @pytest.mark.parametrize("dim", [2, 5])
  def test_map_non_categorical_points_to_unit_hypercube(self, dim):
    domain = form_random_unconstrained_categorical_domain(dim, categoricals_allowed=False)
    num_points = 301
    one_hot_domain = domain.one_hot_domain
    one_hot_points = one_hot_domain.generate_quasi_random_points_in_domain(num_points)
    unit_points = map_non_categorical_points_to_unit_hypercube(one_hot_domain, one_hot_points)
    assert numpy.all(numpy.logical_and(unit_points > 0, unit_points < 1))

    coverted_points = map_non_categorical_points_from_unit_hypercube(one_hot_domain, unit_points)
    assert numpy.allclose(one_hot_points, coverted_points)

  def test_round_one_hot_points_categorical_values_to_target(self):
    first_cat_elements = [1, 2, 6, 9]
    second_cat_elements = [1, 2, 3]
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [2, 5]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": first_cat_elements},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-10, -1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [100, 120]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": second_cat_elements},
      ]
    )
    first_categorical_indices = [1, 2, 3, 4]
    second_categorical_indices = [8, 9, 10]
    num_points = 256
    target_value = 89.9
    one_hot_domain = domain.one_hot_domain
    one_hot_points = one_hot_domain.generate_quasi_random_points_in_domain(num_points)
    rounded_to_target_points = round_one_hot_points_categorical_values_to_target(domain, one_hot_points, target_value)
    sum_first_categorical = numpy.sum(rounded_to_target_points[:, first_categorical_indices], axis=1)
    assert numpy.all(sum_first_categorical == target_value)

    sum_second_categorical = numpy.sum(rounded_to_target_points[:, second_categorical_indices], axis=1)
    assert numpy.all(sum_second_categorical == target_value)

  def test_convert_one_hot_to_search_hypercube_points_distances(self):
    first_cat_elements = [1, 2, 3]
    second_cat_elements = [1, 5, 50, 100]
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-5, -1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [10, 20]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": first_cat_elements},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, -1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5, 5]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": second_cat_elements},
      ]
    )
    points = [
      [-5, 10, 1, -2, -5, 5],  # 0 - min values 1 and '5'
      [-1, 20, 1, -1, 5, 5],  # 1 - max values 1 and '5'
      [-2, 10, 1, -1.9, -1.4, 5],  # 2 - random point in 1 and '5'
      [-5, 10, 2, -2, -5, 5],  # 3 - min values 2 and '5'
      [-5, 10, 3, -2, -5, 5],  # 4 - min values 3 and '5'
      [-5, 10, 1, -2, -5, 1],  # 5 - min values 1 and '1'
      [-5, 10, 1, -2, -5, 50],  # 6 - min values 1 and '50'
      [-5, 10, 3, -2, -5, 50],  # 7 - min values 3 and '50'
      [-1, 20, 3, -1, 5, 100],  # 8 - max values 3 and '100'
    ]
    one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in points])
    search_unit_points = convert_one_hot_to_search_hypercube_points(domain, one_hot_points)

    first_search_point = numpy.atleast_2d(search_unit_points[0])
    distance = numpy.sqrt(compute_distance_matrix_squared(first_search_point, search_unit_points))[0]
    assert distance[0] == 0
    assert distance[1] > distance[2]
    assert distance[3] > distance[1]
    assert distance[3] == distance[4] == distance[5] == distance[6]
    assert distance[7] > distance[3]
    assert distance[8] > distance[7]

  @pytest.mark.parametrize("dim", [3, 7])
  @pytest.mark.parametrize("num_points", [3, 57, 520])
  def test_covert_one_hot_to_search_hypercube_points_distances(self, dim, num_points):
    domain = form_random_unconstrained_categorical_domain(dim)
    one_hot_domain = domain.one_hot_domain
    one_hot_points = one_hot_domain.generate_quasi_random_points_in_domain(num_points)

    search_unit_points = convert_one_hot_to_search_hypercube_points(domain, one_hot_points)

    categorical_indices = []
    for categorical_component_mapping in domain.get_categorical_component_mappings():
      categorical_indices.extend(list(categorical_component_mapping["input_ind_value_map"]))
    non_categorical_indices = list(set(numpy.arange(one_hot_domain.dim)) - set(categorical_indices))
    non_categorical_indices.sort()

    def check_all_elements_are_present(domain, one_hot_points):
      categorical_component_mappings = domain.get_categorical_component_mappings()
      for categorical_component_mapping in categorical_component_mappings:
        cat_indices = list(categorical_component_mapping["input_ind_value_map"])
        best_categories = numpy.argmax(one_hot_points[:, cat_indices], axis=1)
        unique_categories = numpy.unique(best_categories)
        if not len(unique_categories) == len(cat_indices):
          return False
      return True

    if check_all_elements_are_present(domain, one_hot_points):
      is_categorical = numpy.any(search_unit_points > 1, axis=0)
      cat_indices = numpy.arange(one_hot_domain.dim)[is_categorical]
      non_cat_indices = numpy.arange(one_hot_domain.dim)[~is_categorical]
      assert numpy.all(categorical_indices == cat_indices)
      assert numpy.all(non_categorical_indices == non_cat_indices)

    target_value = numpy.sqrt(one_hot_domain.dim)
    num_categories = len(domain.get_categorical_component_mappings())

    sum_categorical_values = numpy.sum(search_unit_points[:, categorical_indices], axis=1)
    assert numpy.allclose(sum_categorical_values, num_categories * target_value)

    lower, upper = one_hot_domain.get_lower_upper_bounds()
    search_lower = convert_one_hot_to_search_hypercube_points(domain, numpy.atleast_2d(lower))
    search_upper = convert_one_hot_to_search_hypercube_points(domain, numpy.atleast_2d(upper))
    assert numpy.all(search_lower[0, non_categorical_indices] == 0)
    assert numpy.all(search_upper[0, non_categorical_indices] == 1)
