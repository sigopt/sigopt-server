# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.compute.misc.constant import CATEGORICAL_POINT_UNIQUENESS_TOLERANCE, DEFAULT_MAX_SIMULTANEOUS_EI_POINTS
from libsigopt.compute.optimization_auxiliary import DEParameters, OptimizerInfo
from libsigopt.compute.search import ProbabilityOfImprovementSearch, SearchAcquisitionFunction
from libsigopt.compute.vectorized_optimizers import DEOptimizer
from libsigopt.compute.views.rest.gp_next_points_categorical import GpNextPointsCategorical, convert_from_one_hot
from libsigopt.compute.views.view import GPView


RESOLVE_PHASE_PROB = 0.8
SEARCH_INITIALIZATION_PHASE = "search_initialization_phase"
SEARCH_EXPLOITATION_PHASE = "search_exploitation_phase"
SEARCH_EXPLORE_RESOLVE_PHASE = "search_explore_resolve_phase"

DEFAULT_SEARCH_OPTIMIZER_INFO = OptimizerInfo(
  optimizer=DEOptimizer,
  parameters=DEParameters(
    crossover_probability=0.7,
    mutation=0.8,
    strategy="best1bin",
  ),
  num_multistarts=100,
  num_random_samples=10000,
)
SEARCH_OPTIMIZER_MAXITER = 200


def get_distance_parameter(dim):
  # random scheduler for search distance parameter
  # values are based on the normalization of the points to a [0, 1]^d hypercube
  distances_squared = [0.04, 0.01, 0.0025, 0.0004]
  distance_parameter = dim * numpy.random.choice(distances_squared, 1)
  return distance_parameter


def search_strategy_optimization(
  acquisition_function,
  num_to_sample,
):
  assert isinstance(acquisition_function, SearchAcquisitionFunction)
  domain = acquisition_function.domain
  initial_repulsor_points = numpy.copy(acquisition_function.repulsor_points)
  initial_distance_parameter = acquisition_function.distance_parameter
  next_points = []
  # the acquisition function is optimized in the one_hot_domain
  pretest_locations = domain.one_hot_domain.generate_quasi_random_points_in_domain(
    DEFAULT_SEARCH_OPTIMIZER_INFO.num_random_samples
  )
  for _ in range(num_to_sample):
    random_af_values = acquisition_function.evaluate_at_point_list(
      pretest_locations,
      batch_size=DEFAULT_MAX_SIMULTANEOUS_EI_POINTS,
    )
    best_af_location = pretest_locations[numpy.argmax(random_af_values), :]
    search_optimizer = DEFAULT_SEARCH_OPTIMIZER_INFO.optimizer(
      domain=domain.one_hot_domain,
      acquisition_function=acquisition_function,
      num_multistarts=DEFAULT_SEARCH_OPTIMIZER_INFO.num_multistarts,
      optimizer_parameters=DEFAULT_SEARCH_OPTIMIZER_INFO.parameters,
      maxiter=SEARCH_OPTIMIZER_MAXITER,
    )
    next_point, _ = search_optimizer.optimize(numpy.atleast_2d(best_af_location))
    assert next_point.shape == (acquisition_function.dim,)
    # add diversity
    acquisition_function.add_normalized_repulsor_point(numpy.atleast_2d(next_point))
    acquisition_function.distance_parameter = get_distance_parameter(domain.dim)
    next_points.append(next_point)
  # revert changes to the acquisition function
  acquisition_function.repulsor_points = initial_repulsor_points
  acquisition_function.distance_parameter = initial_distance_parameter
  optimizer_info_dict = {"es_optimizer": repr(search_optimizer)}
  return numpy.array(next_points), optimizer_info_dict


def identify_search_phase(
  observation_budget,
  observation_count,
  num_open_suggestions,
  failure_count,
):
  INITIALIZATION_FRACTION = 0.2
  EXPLOITATION_FRACTION = 0.4
  adjusted_budget = max(observation_budget - failure_count, max(num_open_suggestions, 1))
  fraction_served = (observation_count + num_open_suggestions) / adjusted_budget

  if fraction_served <= INITIALIZATION_FRACTION:
    return SEARCH_INITIALIZATION_PHASE
  elif fraction_served <= EXPLOITATION_FRACTION:
    return SEARCH_EXPLOITATION_PHASE
  else:
    return SEARCH_EXPLORE_RESOLVE_PHASE


class SearchNextPoints(GPView):
  view_name = "search_next_points"

  def next_points_probability_improvement(self):
    num_to_sample = self.params["num_to_sample"]
    probabilistic_failures = self.form_probabilistic_failures_model()
    repulsor_points = self.one_hot_points_sampled_points
    if len(self.one_hot_points_being_sampled_points) > 0:
      repulsor_points = numpy.concatenate(
        (repulsor_points, self.one_hot_points_being_sampled_points),
        axis=0,
      )
    acquisition_function = ProbabilityOfImprovementSearch(
      domain=self.domain,
      failure_model=probabilistic_failures,
      distance_parameter=get_distance_parameter(self.domain.dim),
      repulsor_points=repulsor_points,
    )
    self.tag.update({"af_info": acquisition_function.info_for_logs})
    one_hot_next_points, optimizer_info = search_strategy_optimization(
      acquisition_function,
      num_to_sample,
    )
    self.tag.update({"optimizer_info": optimizer_info})
    proposed_next_points = convert_from_one_hot(one_hot_next_points, self.domain, acquisition_function)
    return proposed_next_points

  def search_next_points_expected_improvement_with_failures(self):
    if len(self.constraint_metrics_index) == 1:
      return self.search_next_points_expected_improvement()
    optimized_metric = numpy.random.choice(self.constraint_metrics_index)
    constraint_metrics = [i for i in self.params["metrics_info"].constraint_metrics_index if i != optimized_metric]
    view_input = deepcopy(self.params)
    view_input["metrics_info"].optimized_metrics_index = [optimized_metric]
    view_input["metrics_info"].constraint_metrics_index = constraint_metrics
    return GpNextPointsCategorical(view_input).view()

  def search_next_points_expected_improvement(self):
    optimized_metric = numpy.random.choice(self.constraint_metrics_index)
    view_input = deepcopy(self.params)
    view_input["metrics_info"].optimized_metrics_index = [optimized_metric]
    view_input["metrics_info"].constraint_metrics_index = []
    return GpNextPointsCategorical(view_input).view()

  def get_search_phase(self):
    observation_budget = self.params["metrics_info"].observation_budget
    observation_count = len(self.params["points_sampled"].points)
    num_open_suggestions = len(self.one_hot_points_being_sampled_points)
    failure_count = numpy.sum(self.params["points_sampled"].failures)
    return identify_search_phase(
      observation_budget,
      observation_count,
      num_open_suggestions,
      failure_count,
    )

  def view(self):
    assert self.has_constraint_metrics, "Search must have constraint metrics"
    assert not self.has_optimization_metrics, "Search does not support optimization metrics"

    num_to_sample = self.params["num_to_sample"]

    search_phase = self.get_search_phase()
    self.tag.update({"search_phase": search_phase})

    if search_phase is SEARCH_INITIALIZATION_PHASE:
      return self.search_next_points_expected_improvement()
    elif search_phase is SEARCH_EXPLOITATION_PHASE:
      return self.search_next_points_expected_improvement_with_failures()
    else:
      assert search_phase is SEARCH_EXPLORE_RESOLVE_PHASE
      if numpy.random.random() < RESOLVE_PHASE_PROB:
        proposed_next_points = self.next_points_probability_improvement()
      else:
        return self.search_next_points_expected_improvement_with_failures()

    categorical_next_points = self.domain.replace_duplicate_points(
      proposed_next_points,
      self.points_sampled_points,
      tolerance=CATEGORICAL_POINT_UNIQUENESS_TOLERANCE,
    )
    assert len(categorical_next_points) == num_to_sample or self.domain.is_discrete
    results = {
      "endpoint": self.view_name,
      "points_to_sample": categorical_next_points,
      "tag": self.tag,
    }
    return results
