# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME, PARALLEL_QEI, TASK_SELECTION_STRATEGY_A_PRIORI
from libsigopt.compute.acquisition_function_optimization import (
  constant_liar_acquisition_function_optimization,
  qei_acquisition_function_optimization,
)
from libsigopt.compute.domain import CategoricalDomain, FixedIndicesOnContinuousDomain
from libsigopt.compute.expected_improvement import ExpectedParallelImprovement
from libsigopt.compute.misc.constant import CATEGORICAL_POINT_UNIQUENESS_TOLERANCE
from libsigopt.compute.multitask_acquisition_function import MultitaskAcquisitionFunction
from libsigopt.compute.views.view import GPView


MAXIMUM_NEIGHBORING_POINTS = 30000
MAXIMUM_INT_COMPONENTS = 14
MAXIMUM_PRODUCT_OF_CATS = 4000


def select_random_task_by_softmax(task_options, size=None):
  relative_probabilities = numpy.exp(-task_options) / numpy.sum(numpy.exp(-task_options))
  return numpy.random.choice(task_options, p=relative_probabilities, size=size)


def generate_neighboring_integer_points(one_hot_point, domain):
  integer_component_mappings = domain.get_integer_component_mappings()
  neighboring_points = numpy.tile(one_hot_point, [2] * len(integer_component_mappings) + [1])
  for index_within_integers, integer_component_mapping in enumerate(integer_component_mappings):
    one_hot_integer_value = one_hot_point[integer_component_mapping["input_ind"]]
    slices = [slice(None)] * len(integer_component_mappings) + [integer_component_mapping["input_ind"]]
    slices[index_within_integers] = slice(0, 1)
    neighboring_points[tuple(slices)] = numpy.floor(one_hot_integer_value)
    slices[index_within_integers] = slice(1, 2)
    neighboring_points[tuple(slices)] = numpy.ceil(one_hot_integer_value)
  return numpy.reshape(neighboring_points, (2 ** len(integer_component_mappings), len(one_hot_point)))


def generate_neighboring_categorical_points(one_hot_points, domain):
  # enforcing 2d array so the following operations can be vectorized
  num_one_hot_points, one_hot_dim = one_hot_points.shape
  # assert len(one_hot_points_shape) == 2

  categorical_component_mappings = domain.get_categorical_component_mappings()
  product_of_cats = domain.product_of_categories
  # For each neighboring point, we need to create product_of_cats neighboring categorical points
  neighboring_points = numpy.reshape(
    numpy.tile(one_hot_points, (1, product_of_cats)), (num_one_hot_points, product_of_cats, one_hot_dim)
  )
  remaining_product_of_cats = product_of_cats
  running_product_of_cats = 1

  # each one_hot_point has product_of_cats many neighboring categorical points.
  # suppose the domain is CategoricalDomain([
  # {'var_type': 'double', 'elements': [0, 1]},
  # {'var_type': 'categorical', 'elements': ['cats', 'dogs']},
  # {'var_type': 'categorical', 'elements': ['s', 't']},
  # ])
  # This results in a 5D one_hot_point, e.g. [0.1, 0.9, 0.1, 0.4, 0.2]. The neighboring categorical points would be
  # [
  #   [0.1, 1, 0, 1, 0]
  #   [0.1, 1, 0, 0, 1]
  #   [0.1, 0, 1, 1, 0]
  #   [0.1, 0, 1, 0, 1]
  #  ]
  for categorical_component_mapping in categorical_component_mappings:
    cat_indices = list(categorical_component_mapping["input_ind_value_map"].keys())
    num_of_cat_indices = len(cat_indices)
    remaining_product_of_cats //= num_of_cat_indices
    neighboring_points[:, :, cat_indices] = numpy.reshape(
      numpy.tile(numpy.eye(num_of_cat_indices), (running_product_of_cats, remaining_product_of_cats)),
      (product_of_cats, num_of_cat_indices),
    )
    running_product_of_cats *= num_of_cat_indices

  return numpy.reshape(neighboring_points, (num_one_hot_points * product_of_cats, one_hot_dim))


def find_best_one_hot_neighbor_by_af(one_hot_points, domain, acquisition_function, option):
  if option == "none":
    return one_hot_points

  # Choose the best integer-valued point neighboring each one hot point
  discrete_rounded_one_hot_points = []
  for one_hot_point in one_hot_points:
    if option == "cat":
      neighboring_snapped_points_in_one_hot = generate_neighboring_categorical_points(
        numpy.atleast_2d(one_hot_point),
        domain,
      )
      neighboring_snapped_points_in_one_hot = domain.round_one_hot_points_integer_values(
        neighboring_snapped_points_in_one_hot,
      )
    elif option == "int":
      neighboring_snapped_points_in_one_hot = generate_neighboring_integer_points(one_hot_point, domain)
      neighboring_snapped_points_in_one_hot = domain.round_one_hot_points_categorical_values(
        neighboring_snapped_points_in_one_hot,
      )
    else:
      neighboring_int_points = generate_neighboring_integer_points(one_hot_point, domain)
      neighboring_snapped_points_in_one_hot = generate_neighboring_categorical_points(neighboring_int_points, domain)
    neighboring_snapped_points_in_one_hot = domain.round_one_hot_points_quantized_values(
      neighboring_snapped_points_in_one_hot,
    )
    neighboring_snapped_ei_vals = acquisition_function.evaluate_at_point_list(neighboring_snapped_points_in_one_hot)
    best_discrete_neighbor_in_one_hot, _ = max(
      zip(neighboring_snapped_points_in_one_hot, neighboring_snapped_ei_vals),
      key=lambda x: x[1],
    )
    discrete_rounded_one_hot_points.append(best_discrete_neighbor_in_one_hot)
  return discrete_rounded_one_hot_points


def get_discrete_conversion_option(domain):
  number_of_integer_components = len(domain.get_integer_component_mappings())
  product_of_cats = domain.product_of_categories
  option = "none"
  if (
    0 < number_of_integer_components <= MAXIMUM_INT_COMPONENTS
    and 1 < product_of_cats <= MAXIMUM_PRODUCT_OF_CATS
  ):
    if product_of_cats * (2**number_of_integer_components) <= MAXIMUM_NEIGHBORING_POINTS:
      option = "both"
    else:
      option = "int"  # prioritize integer snapping since it's much cheaper
  elif product_of_cats > MAXIMUM_PRODUCT_OF_CATS or product_of_cats == 1:
    option = "int" if 0 < number_of_integer_components <= MAXIMUM_INT_COMPONENTS else "none"
  elif number_of_integer_components > MAXIMUM_INT_COMPONENTS or number_of_integer_components == 0:
    option = "cat" if 1 < product_of_cats <= MAXIMUM_PRODUCT_OF_CATS else "none"
  else:
    option = "none"
  return option


# TODO(RTL-76): Push this further into the optimization process to take advantage of the CL computations
# TODO(RTL-77): Need to come up with strategy for dealing with a finite domain but having noise
# TODO(RTL-78): Need to think about the implications for this in the QEI setting (or a workaround)
def convert_from_one_hot(one_hot_points, domain, acquisition_function, temperature=None):
  option = get_discrete_conversion_option(domain)
  if (
    isinstance(acquisition_function, ExpectedParallelImprovement)
    or domain.is_integer_constrained
  ):
    option = "none"
  discrete_one_hot_neighbors = find_best_one_hot_neighbor_by_af(
    one_hot_points=one_hot_points,
    domain=domain,
    acquisition_function=acquisition_function,
    option=option,
  )
  return domain.map_one_hot_points_to_categorical(discrete_one_hot_neighbors, temperature=temperature)


# TODO(RTL-79): Think where this function really belongs
def snap_continuous_tasks_to_discrete_options(task_costs, task_options):
  distance_from_tasks = numpy.abs(task_costs[:, None] - task_options[None, :])
  return task_options[numpy.argmin(distance_from_tasks, axis=1)]


def _form_domain_with_task_dimension(domain, acquisition_function=None, task_options=None):
  assert acquisition_function is None or isinstance(acquisition_function, MultitaskAcquisitionFunction)
  domain_components = deepcopy(domain.domain_components)
  constraint_list = deepcopy(domain.constraint_list)
  force_hitandrun_sampling = domain.force_hitandrun_sampling

  task_elements = [0.0, 1.0]
  if task_options is not None and task_options.size:
    task_elements = [min(task_options), max(task_options)]
  domain_components.append({"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": task_elements})

  for this_constraint in constraint_list:
    this_constraint["weights"] = numpy.append(this_constraint["weights"], 0)

  return CategoricalDomain(domain_components, constraint_list, force_hitandrun_sampling)


def _form_domain_for_qei_parallelism(domain, acquisition_function):
  assert acquisition_function.dim == domain.one_hot_dim
  assert not isinstance(acquisition_function, MultitaskAcquisitionFunction)
  num_points_to_sample = acquisition_function.num_points_to_sample
  assert num_points_to_sample > 1

  domain_components = deepcopy(domain.domain_components)
  constraint_list = deepcopy(domain.constraint_list)
  force_hitandrun_sampling = domain.force_hitandrun_sampling

  domain_components *= num_points_to_sample
  extended_constraint_list = []
  for this_constraint in constraint_list:
    base_weights = this_constraint["weights"]
    no_constraint = [0] * len(base_weights)
    for i in range(num_points_to_sample):
      extended_weights = []
      for j in range(num_points_to_sample):
        extended_weights.extend(base_weights if i == j else no_constraint)
      extended_constraint_list.append(
        {
          "weights": extended_weights,
          "rhs": this_constraint["rhs"],
          "var_type": this_constraint["var_type"],
        }
      )
  constraint_list = extended_constraint_list

  augmented_domain = CategoricalDomain(domain_components, constraint_list, force_hitandrun_sampling)
  assert acquisition_function.dim * acquisition_function.num_points_to_sample == augmented_domain.one_hot_dim

  return augmented_domain


def form_augmented_domain(domain, acquisition_function=None, task_cost_populated=False, task_options=None):
  if task_cost_populated:
    return _form_domain_with_task_dimension(domain, acquisition_function, task_options)

  if acquisition_function is not None:
    assert acquisition_function.dim == domain.one_hot_dim
    if acquisition_function.num_points_to_sample > 1:
      return _form_domain_for_qei_parallelism(domain, acquisition_function)

  return domain


class GpNextPointsCategorical(GPView):
  view_name = "gp_next_points_categorical"

  def form_af_optimization_domain(self, acquisition_function):
    augmented_one_hot_domain = form_augmented_domain(
      domain=self.domain,
      acquisition_function=acquisition_function,
      task_cost_populated=self.task_cost_populated,
      task_options=self.task_options,
    ).one_hot_domain
    if isinstance(acquisition_function, MultitaskAcquisitionFunction):
      model_info = self.params["model_info"]
      assert model_info.task_selection_strategy == TASK_SELECTION_STRATEGY_A_PRIORI
      task_chosen_a_priori = select_random_task_by_softmax(self.task_options)
      fixed_indices = {self.dim_with_task - 1: task_chosen_a_priori}
      augmented_one_hot_domain = FixedIndicesOnContinuousDomain(augmented_one_hot_domain, fixed_indices)
    return augmented_one_hot_domain

  def _convert_one_hot_points_for_multitask(self, one_hot_next_points, acquisition_function):
    domain_with_task = form_augmented_domain(
      self.domain,
      task_cost_populated=self.task_cost_populated,
      task_options=self.task_options,
    )
    proposed_next_points = convert_from_one_hot(one_hot_next_points, domain_with_task, acquisition_function)
    augmented_points_sampled_points = domain_with_task.map_one_hot_points_to_categorical(
      self.one_hot_points_sampled_points,
    )
    categorical_next_points = domain_with_task.replace_duplicate_points(
      proposed_next_points,
      augmented_points_sampled_points,
      tolerance=CATEGORICAL_POINT_UNIQUENESS_TOLERANCE,
    )
    next_points_task_costs = snap_continuous_tasks_to_discrete_options(
      categorical_next_points[:, -1],
      self.task_options,
    )
    categorical_next_points = categorical_next_points[:, :-1]
    return categorical_next_points, next_points_task_costs

  def convert_one_hot_points_to_distinct_categorical_points(self, one_hot_next_points, acquisition_function):
    if self.task_cost_populated:
      return self._convert_one_hot_points_for_multitask(one_hot_next_points, acquisition_function)
    proposed_next_points = convert_from_one_hot(one_hot_next_points, self.domain, acquisition_function)
    categorical_next_points = self.domain.replace_duplicate_points(
      proposed_next_points,
      self.points_sampled_points,
      tolerance=CATEGORICAL_POINT_UNIQUENESS_TOLERANCE,
    )
    next_points_task_costs = None
    return categorical_next_points, next_points_task_costs

  def view(self):
    assert self.has_optimization_metrics, f"{self.view_name} must have optimization metrics"
    num_to_sample = self.params["num_to_sample"]
    parallelism = self.params["parallelism"]

    gaussian_process = self.form_gaussian_process_for_acquisition_function()
    num_being_sampled = len(self.one_hot_points_being_sampled_points)
    probabilistic_failures = self.form_probabilistic_failures_model()
    use_parallel_ei = (
      num_being_sampled > 0
      and parallelism == PARALLEL_QEI
      and not self.task_cost_populated
    )
    acquisition_function = self.form_acquisition_function(
      gaussian_process=gaussian_process,
      probabilistic_failures=probabilistic_failures,
      use_parallel_ei=use_parallel_ei,
    )
    if not use_parallel_ei and self.task_cost_populated:
      acquisition_function = MultitaskAcquisitionFunction(acquisition_function)
    af_optimization_domain = self.form_af_optimization_domain(acquisition_function)

    if use_parallel_ei:
      one_hot_next_points_unshaped, optimizer_info = qei_acquisition_function_optimization(
        af_optimization_domain,
        acquisition_function,
      )
      one_hot_next_points = numpy.reshape(one_hot_next_points_unshaped, (num_to_sample, self.dim_with_task))
    else:
      one_hot_next_points, optimizer_info = constant_liar_acquisition_function_optimization(
        af_optimization_domain,
        acquisition_function,
        num_to_sample,
      )
    self.tag.update({"optimizer_info": optimizer_info})

    categorical_next_points, next_points_task_costs = self.convert_one_hot_points_to_distinct_categorical_points(
      one_hot_next_points,
      acquisition_function,
    )

    # It is possible for a discrete domain to exhaust all the points, so we may return fewer points than requested
    assert len(categorical_next_points) == num_to_sample or self.domain.is_discrete
    acceptable = [self.domain.check_point_acceptable(p) for p in categorical_next_points]

    results = {
      "acceptable": acceptable,
      "endpoint": self.view_name,
      "points_to_sample": categorical_next_points,
      "tag": self.tag,
    }
    if next_points_task_costs is not None:
      results["task_costs"] = next_points_task_costs.tolist()
    return results
