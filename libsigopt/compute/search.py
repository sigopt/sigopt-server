# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import dataclass

import numpy

from libsigopt.aux.geometry_utils import compute_distance_matrix_squared
from libsigopt.compute.acquisition_function import AcquisitionFunction
from libsigopt.compute.domain import CategoricalDomain, ContinuousDomain
from libsigopt.compute.predictor import Predictor
from libsigopt.compute.probabilistic_failures import ProbabilisticFailuresBase


@dataclass(frozen=True, slots=True)
class SearchCoreComponents:
  search_points_to_evaluate: numpy.ndarray
  pi: numpy.ndarray
  pi_grad: numpy.ndarray


class FakePredictor(Predictor):
  def __init__(self):
    self.best_observed_value = None
    self.best_observed_location = None


class SearchAcquisitionFunction(AcquisitionFunction):
  def __init__(self, domain, failure_model):
    assert isinstance(domain, CategoricalDomain)
    assert isinstance(failure_model, ProbabilisticFailuresBase)
    # This dummy predictor allow us to use vectorized optimizers, needed due to
    # due to AcquisitionFunction(HasPredictor). This predcitor is never used
    super().__init__(FakePredictor())
    self.domain = domain
    self.failure_model = failure_model
    self.repulsor_points = numpy.empty((0, self.dim))

  @property
  def differentiable(self):
    return False

  @property
  def info_for_logs(self):
    raise NotImplementedError()

  @property
  def dim(self):
    return self.failure_model.dim

  def _evaluate_at_point_list(self, points_to_evaluate):
    return self._evaluate_at_point_list_normalized(self.compute_core_components(points_to_evaluate, "func"))

  def _evaluate_at_point_list_normalized(self, core_components):
    raise NotImplementedError()

  def add_normalized_repulsor_point(self, one_hot_points):
    assert len(one_hot_points.shape) == 2
    assert one_hot_points.shape[1] == self.dim
    search_points = convert_one_hot_to_search_hypercube_points(self.domain, one_hot_points)
    self.repulsor_points = numpy.append(self.repulsor_points, search_points, axis=0)

  def compute_core_components(self, points_to_evaluate, option):
    assert option == "func"
    eval_shape = points_to_evaluate.shape
    assert len(eval_shape) == 2 and eval_shape[1] == self.dim
    search_points_to_evaluate = convert_one_hot_to_search_hypercube_points(self.domain, points_to_evaluate)
    pi_grad = None
    if option in ("func",):
      pi = self.failure_model.compute_probability_of_success(points_to_evaluate)
    return SearchCoreComponents(search_points_to_evaluate, pi, pi_grad)


class ProbabilityOfImprovementSearch(SearchAcquisitionFunction):
  def __init__(self, domain, failure_model, distance_parameter, repulsor_points=None):
    super().__init__(domain, failure_model)
    self.distance_parameter = distance_parameter
    if repulsor_points is not None:
      self.add_normalized_repulsor_point(repulsor_points)

  @property
  def info_for_logs(self):
    return {
      "failure_model": self.failure_model.info_for_logs,
      "distance_parameter": self.distance_parameter,
      "repulsor_points": self.repulsor_points,
    }

  def _evaluate_at_point_list_normalized(self, core_components):
    probability_of_improvement = core_components.pi
    distance = compute_distance_matrix_squared(self.repulsor_points, core_components.search_points_to_evaluate)
    similar_indices = numpy.any(distance < self.distance_parameter, axis=0)
    probability_of_improvement[similar_indices] = 0
    return probability_of_improvement


def round_one_hot_points_categorical_values_to_target(domain, one_hot_points, target):
  if not domain.has_categoricals:
    return one_hot_points

  categorical_component_mappings = domain.get_categorical_component_mappings()
  for categorical_component_mapping in categorical_component_mappings:
    cat_indices = list(categorical_component_mapping["input_ind_value_map"])
    best_categories = numpy.argmax(one_hot_points[:, cat_indices], axis=1)
    one_hot_points[:, cat_indices] = 0
    one_hot_points[range(len(one_hot_points)), cat_indices[0] + best_categories] = target
  return one_hot_points


def map_non_categorical_points_to_unit_hypercube(one_hot_domain, one_hot_points):
  assert isinstance(one_hot_domain, ContinuousDomain)
  assert one_hot_domain.dim == one_hot_points.shape[1]
  lower, upper = one_hot_domain.get_lower_upper_bounds()
  return (one_hot_points - lower) / (upper - lower)


def map_non_categorical_points_from_unit_hypercube(one_hot_domain, unit_search_points):
  assert isinstance(one_hot_domain, ContinuousDomain)
  assert one_hot_domain.dim == unit_search_points.shape[1]
  lower, upper = one_hot_domain.get_lower_upper_bounds()
  return (unit_search_points) * (upper - lower) + lower


# Note: consider making this a class function for SearchAF or PISearch
# The "search hypercube" has non categorical values normalized between [0, 1] and categorical
# values ranging from [0, sqrt(d)], where d is one_hot_dim > number of non categorical values
# The goal is to make points with different categories far from each other
def convert_one_hot_to_search_hypercube_points(domain, one_hot_points):
  assert isinstance(domain, CategoricalDomain)
  unit_one_hot_points = map_non_categorical_points_to_unit_hypercube(domain.one_hot_domain, one_hot_points)
  largest_distance = numpy.sqrt(domain.one_hot_dim)
  return round_one_hot_points_categorical_values_to_target(domain, unit_one_hot_points, largest_distance)
