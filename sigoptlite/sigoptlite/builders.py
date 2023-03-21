# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import itertools

import numpy

from sigoptaux.constant import (
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MAX_NUM_INT_CONSTRAINT_VARIABLES,
  ConstraintType,
  ParameterTransformationNames,
)
from sigoptaux.geometry_utils import find_interior_point
from sigoptlite.models import *


def create_experiment_from_template(experiment_template, **kwargs):
  experiment_meta = dataclass_to_dict(experiment_template)
  experiment_meta.update(kwargs)
  return LocalExperimentBuilder(experiment_meta)


class BuilderBase(object):
  def __new__(cls, input_dict):
    cls.validate_input_dict(input_dict)
    local_object = cls.create_object(**input_dict)
    cls.validate_object(local_object)
    return local_object

  @classmethod
  def validate_input_dict(cls, input_dict):
    raise NotImplementedError

  @classmethod
  def create_object(cls, **input_dict):
    raise NotImplementedError

  @classmethod
  def validate_object(cls, _):
    pass

  @classmethod
  def set_object(cls, input_dict, field, local_class):
    if not input_dict.get(field):
      return
    input_dict[field] = local_class(input_dict[field])

  @classmethod
  def set_list_of_objects(cls, input_dict, field, local_class):
    if not input_dict.get(field):
      return
    input_dict[field] = [local_class(i) for i in input_dict[field]]

  @staticmethod
  def get_num_distict_elements(lst):
    return len(set(lst))


class LocalExperimentBuilder(BuilderBase):
  cls_name = "sigoptlite experiment"

  @classmethod
  def validate_input_dict(cls, input_dict):
    assert isinstance(input_dict["parameters"], list)
    assert len(input_dict["parameters"]) > 0
    assert isinstance(input_dict["metrics"], list)
    assert len(input_dict["metrics"]) > 0

  @classmethod
  def create_object(cls, **input_dict):
    cls.set_list_of_objects(input_dict, field="parameters", local_class=LocalParameterBuilder)
    cls.set_list_of_objects(input_dict, field="metrics", local_class=LocalMetricBuilder)
    cls.set_list_of_objects(input_dict, field="conditionals", local_class=LocalConditionalBuilder)
    cls.set_list_of_objects(input_dict, field="tasks", local_class=LocalTaskBuilder)
    cls.set_list_of_objects(input_dict, field="linear_constraints", local_class=LocalLinearConstraintBuilder)
    return LocalExperiment(**input_dict)

  @classmethod
  def validate_object(cls, experiment):
    cls.validate_parameters(experiment)
    cls.validate_metrics(experiment)

    if not experiment.parallel_bandwidth == 1:
      raise ValueError(f"{cls.cls_name} must have parallel_bandwidth == 1")

    observation_budget = experiment.observation_budget
    if observation_budget is None:
      if experiment.num_solutions > 1:
        raise ValueError(f"observation_budget is required for a {cls.cls_name} with multiple solutions")
      if experiment.requires_pareto_frontier_optimization:
        raise ValueError(f"observation_budget is required for a {cls.cls_name} with more than one optimized metric")
      if experiment.has_constraint_metrics:
        raise ValueError(f"observation_budget is required for a {cls.cls_name} with constraint metrics")
      if experiment.is_multitask:
        raise ValueError(f"observation_budget is required for a {cls.cls_name} with tasks (multitask)")

    if not (experiment.optimized_metrics or experiment.constraint_metrics):
      raise ValueError(f"{cls.cls_name} must have optimized or constraint metrics")

    if experiment.optimized_metrics:
      if not len(experiment.optimized_metrics) in [1, 2]:
        raise ValueError(f"{cls.cls_name} must have one or two optimized metrics")

    # Check feature viability of multisolution experiments
    num_solutions = experiment.num_solutions
    if num_solutions and num_solutions > 1:
      if num_solutions > observation_budget:
        raise ValueError("observation_budget needs to be larger than the number of solutions")
      if not len(experiment.optimized_metrics) == 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions require exactly one optimized metric")

    # Check conditional limitation
    if experiment.is_conditional:
      if num_solutions and num_solutions > 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions does not support conditional parameters")
      if experiment.is_search:
        raise ValueError(f"All-Constraint {cls.cls_name} does not support conditional parameters")
      cls.validate_conditionals(experiment)

    # Check feature viability of multitask
    tasks = experiment.tasks
    if tasks:
      if experiment.requires_pareto_frontier_optimization:
        raise ValueError(f"{cls.cls_name} cannot have both tasks and multiple optimized metrics")
      if experiment.has_constraint_metrics:
        raise ValueError(f"{cls.cls_name} cannot have both tasks and constraint metrics")
      if num_solutions and num_solutions > 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions cannot be multitask")
      cls.validate_tasks(experiment)

    if experiment.linear_constraints:
      cls.validate_constraints(experiment)
      cls.check_constraint_feasibility(experiment)

  @classmethod
  def validate_parameters(cls, experiment):
    param_names = [p.name for p in experiment.parameters]
    if not len(param_names) == cls.get_num_distict_elements(param_names):
      raise ValueError(f"No duplicate parameters are allowed: {param_names}")

  @classmethod
  def validate_metrics(cls, experiment):
    metric_names = [m.name for m in experiment.metrics]
    if not len(metric_names) == cls.get_num_distict_elements(metric_names):
      raise ValueError(f"No duplicate metrics are allowed: {metric_names}")

  @classmethod
  def validate_conditionals(cls, experiment):
    cls.check_all_conditional_values_satisfied(experiment)

  @classmethod
  def validate_tasks(cls, experiment):
    if len(experiment.tasks) < 2:
      raise ValueError("For multitask experiments, at least 2 tasks must be present.")
    costs = [t.cost for t in experiment.tasks]
    num_distinct_task = cls.get_num_distict_elements([t.name for t in experiment.tasks])
    num_distinct_costs = cls.get_num_distict_elements(costs)
    if not num_distinct_task == len(experiment.tasks):
      raise ValueError(f"For multitask {cls.cls_name}, all task names must be distinct")
    if not num_distinct_costs == len(experiment.tasks):
      raise ValueError(f"For multitask {cls.cls_name}, all costs names must be distinct")
    if 1 not in costs:
      raise ValueError(f"For multitask {cls.cls_name}, exactly one task must have cost == 1 (none present).")

  @classmethod
  def validate_constraints(cls, experiment):
    parameter_names = []
    double_params_names = []
    integer_params_names = []
    unconditioned_params_names = []
    log_transform_params_names = []
    grid_param_names = []
    for p in experiment.parameters:
      parameter_names.append(p.name)
      if p.grid:
        grid_param_names.append(p.name)
      if p.type == DOUBLE_EXPERIMENT_PARAMETER_NAME:
        double_params_names.append(p.name)
      if p.type == INT_EXPERIMENT_PARAMETER_NAME:
        integer_params_names.append(p.name)
      if p.type in [DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME]:
        if not p.conditions:
          unconditioned_params_names.append(p.name)
        if p.transformation == ParameterTransformationNames.LOG:
          log_transform_params_names.append(p.name)

    constrained_integer_variables = set()
    for c in experiment.linear_constraints:
      terms = c.terms
      constraint_var_set = set()
      if len(terms) <= 1:
        raise ValueError("Constraint must have more than one term")

      term_types = []
      for term in terms:
        coeff = term.weight
        if coeff == 0:
          continue
        name = term.name
        if name in integer_params_names:
          constrained_integer_variables.add(name)
        if len(constrained_integer_variables) > MAX_NUM_INT_CONSTRAINT_VARIABLES:
          raise ValueError(
            f"{cls.cls_name} allows no more than {MAX_NUM_INT_CONSTRAINT_VARIABLES} integer constraint variables"
          )
        if name not in parameter_names:
          raise ValueError(f"Variable {name} is not a known parameter")
        if name not in double_params_names and name not in integer_params_names:
          raise ValueError(f"Variable {name} is not a parameter of type `double` or type `int`")
        else:
          term_types.append(
            DOUBLE_EXPERIMENT_PARAMETER_NAME if name in double_params_names else INT_EXPERIMENT_PARAMETER_NAME
          )
        if name not in unconditioned_params_names:
          raise ValueError(f"Constraint cannot be defined on a conditioned parameter {name}")
        if name in log_transform_params_names:
          raise ValueError(f"Constraint cannot be defined on a log-transformed parameter {name}")
        if name in grid_param_names:
          raise ValueError(f"Constraint cannot be defined on a grid parameter {name}")
        if name in constraint_var_set:
          raise ValueError(f"Duplicate variable name: {name}")
        else:
          constraint_var_set.add(name)

      if len(set(term_types)) > 1:
        raise ValueError("Constraint functions cannot mix integers and doubles. One or the other only.")

  @classmethod
  def check_constraint_feasibility(cls, experiment):
    def parse_constraints_to_halfspaces(constraints, parameters):
      constrained_parameters_names = []
      for constraint in constraints:
        constrained_parameters_names += [term.name for term in constraint.terms]
      constrained_parameters_names = list(set(constrained_parameters_names))

      constrained_parameters = [p for p in parameters if p.name in constrained_parameters_names]
      dim = len(constrained_parameters)
      num_explicit_constraints = len(constraints)
      n_halfspaces = 2 * dim + num_explicit_constraints
      halfspaces = numpy.zeros((n_halfspaces, dim + 1))

      for ic, constraint in enumerate(constraints):
        # Invert less_than constraints
        assert constraint.type in (ConstraintType.greater_than, ConstraintType.less_than)
        sign = -1 if constraint.type == ConstraintType.less_than else 1

        halfspaces[ic, -1] = sign * constraint.threshold
        nonzero_coef_map = {a.name: a.weight for a in constraint.terms}
        for ip, p in enumerate(constrained_parameters):
          if p.name in nonzero_coef_map:
            halfspaces[ic, ip] = -sign * nonzero_coef_map[p.name]

      for index, p in enumerate(constrained_parameters):
        imin = num_explicit_constraints + 2 * index
        imax = num_explicit_constraints + 2 * index + 1

        halfspaces[imin, -1] = p.bounds.min
        halfspaces[imax, -1] = -p.bounds.max
        halfspaces[imin, index] = -1
        halfspaces[imax, index] = 1

      return halfspaces

    halfspaces = parse_constraints_to_halfspaces(experiment.linear_constraints, experiment.parameters)
    _, _, feasibility = find_interior_point(halfspaces)
    if not feasibility:
      raise ValueError("Infeasible constraints")

  @staticmethod
  def check_all_conditional_values_satisfied(experiment):
    num_conditional_values = numpy.product([len(c.values) for c in experiment.conditionals])
    satisfied_parameter_configurations = set([])
    for parameter in experiment.parameters:
      conditional_values = []
      for conditional in experiment.conditionals:
        parameter_conditions = {x.name: x.values for x in parameter.conditions}
        if conditional.name in parameter_conditions:
          conditional_values.append(parameter_conditions[conditional.name])
        else:  # If that conditional is not present for a parameter, then add all values
          conditional_values.append([x.name for x in conditional.values])
      for selected_conditionals in itertools.product(*conditional_values):
        satisfied_parameter_configurations.add(selected_conditionals)

    if len(satisfied_parameter_configurations) != num_conditional_values:
      raise ValueError("Need at least one parameter that satisfies each conditional value")


class LocalParameterBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert isinstance(input_dict["name"], str)
    assert isinstance(input_dict["type"], str)

  @classmethod
  def create_object(cls, **input_dict):
    cls.set_object(input_dict, field="bounds", local_class=LocalBoundsBuilder)
    if input_dict.get("categorical_values"):
      categorical_values = input_dict["categorical_values"]
      get_name_options = {str: lambda x: x, dict: lambda x: x["name"]}
      get_name = get_name_options[type(categorical_values[0])]
      sorted_categorical_values = sorted(categorical_values, key=get_name)
      input_dict["categorical_values"] = [
        LocalCategoricalValue(name=get_name(cv), enum_index=i + 1) for i, cv in enumerate(sorted_categorical_values)
      ]
    if input_dict.get("conditions"):
      input_dict["conditions"] = [LocalCondition(name=n, values=v) for n, v in input_dict["conditions"].items()]
    cls.set_object(input_dict, field="prior", local_class=LocalParameterPriorBuilder)
    return LocalParameter(**input_dict)

  @classmethod
  def validate_object(cls, parameter):
    # categorical parameter
    if parameter.is_categorical:
      if not len(parameter.categorical_values) > 1:
        raise ValueError(
          f"Categorical parameter {parameter.name} must have more than one categorical value. "
          f"Current values are {parameter.categorical_values}"
        )
      if parameter.grid:
        raise ValueError("Categorical parameter does not support grid values")
      if parameter.bounds:
        raise ValueError(f"Categorical parameter should not have bounds: {parameter.bounds}")

    # parameter with grid
    if parameter.grid:
      if not len(parameter.grid) > 1:
        raise ValueError(
          f"Grid parameter {parameter.name} must have more than one value. Current values are {parameter.grid}"
        )
      if parameter.bounds:
        raise ValueError(f"Grid parameter should not have bounds: {parameter.bounds}")
      if not cls.get_num_distict_elements(parameter.grid) == len(parameter.grid):
        raise ValueError(f"Grid values should be unique: {parameter.grid}")

    # log transformation
    if parameter.has_transformation:
      if not parameter.is_double:
        raise ValueError("Transformation only applies to parameters type of double")
      if parameter.bounds and parameter.bounds.min <= 0:
        raise ValueError("Invalid bounds for log-transformation: bounds must be positive")
      if parameter.grid and min(parameter.grid) <= 0:
        raise ValueError("Invalid grid values for log-transformation: values must be positive")

    # parameter priors
    if parameter.has_prior:
      if not parameter.is_double:
        raise ValueError("Prior only applies to parameters type of double")
      if parameter.prior.is_normal:
        if not parameter.bounds.is_value_within(parameter.prior.mean):
          raise ValueError(f"parameter.prior.mean {parameter.prior.mean} must be within bounds {parameter.bounds}")
      if not (parameter.prior.is_normal ^ parameter.prior.is_beta):
        raise ValueError(f"{parameter.prior} must be either normal or beta")


class LocalMetricBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert isinstance(input_dict["name"], str)

  @classmethod
  def create_object(cls, **input_dict):
    return LocalMetric(**input_dict)


class LocalConditionalBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert set(input_dict.keys()) == {"name", "values"}
    assert isinstance(input_dict["name"], str)
    assert isinstance(input_dict["values"], list)

  @classmethod
  def create_object(cls, **input_dict):
    input_dict["values"] = [LocalConditionalValue(enum_index=i + 1, name=v) for i, v in enumerate(input_dict["values"])]
    return LocalConditional(**input_dict)


class LocalTaskBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert set(input_dict.keys()) == {"name", "cost"}
    assert isinstance(input_dict["name"], str)
    assert isinstance(input_dict["cost"], (int, float))

  @classmethod
  def create_object(cls, **input_dict):
    return LocalTask(**input_dict)

  @classmethod
  def validate_object(cls, task):
    if task.cost <= 0 or task.cost > 1:
      raise ValueError(f"{task} costs must be positve and less than or equal to 1.")


class LocalLinearConstraintBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert input_dict.keys() == {"type", "terms", "threshold"}
    assert input_dict["type"] in ["less_than", "greater_than"]
    assert isinstance(input_dict["threshold"], (int, float))

  @classmethod
  def create_object(cls, **input_dict):
    cls.set_list_of_objects(input_dict, field="terms", local_class=LocalConstraintTermBuilder)
    return LocalLinearConstraint(**input_dict)


class LocalBoundsBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert set(input_dict.keys()) == {"min", "max"}
    assert isinstance(input_dict["min"], (int, float))
    assert isinstance(input_dict["max"], (int, float))

  @classmethod
  def create_object(cls, **input_dict):
    return LocalBounds(**input_dict)

  @classmethod
  def validate_object(cls, bounds):
    if bounds.min >= bounds.max:
      raise ValueError(f"{bounds}: min must be less than max")


class LocalParameterPriorBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert input_dict["name"] in ["beta", "normal"]

  @classmethod
  def create_object(cls, **input_dict):
    return LocalParameterPrior(**input_dict)

  @classmethod
  def validate_object(cls, parameter_prior):
    if parameter_prior.is_beta:
      if (parameter_prior.shape_a is None) or (parameter_prior.shape_b is None):
        raise ValueError(f"{parameter_prior} must have shape_a and shape_b")
      if parameter_prior.shape_a <= 0:
        raise ValueError(f"{parameter_prior} shape_a must be positive")
      if parameter_prior.shape_b <= 0:
        raise ValueError(f"{parameter_prior} shape_b must be positive")
    if parameter_prior.is_normal:
      if (parameter_prior.mean is None) or (parameter_prior.scale is None):
        raise ValueError(f"{parameter_prior} must provide mean and scale")
      if parameter_prior.scale <= 0:
        raise ValueError(f"{parameter_prior} scale must be positive")


class LocalConstraintTermBuilder(BuilderBase):
  @classmethod
  def validate_input_dict(cls, input_dict):
    assert set(input_dict.keys()) == {"name", "weight"}
    assert isinstance(input_dict["name"], str)
    assert isinstance(input_dict["weight"], (int, float))

  @classmethod
  def create_object(cls, **input_dict):
    return LocalConstraintTerm(**input_dict)


class LocalObservationBuilder(object):
  @classmethod
  def validate_observation_dict(cls, observation_dict):
    assert len(observation_dict["assignments"]) > 0
    if observation_dict.get("values") is not None:
      assert len(observation_dict["values"]) > 0
      failed = observation_dict.get("failed", False)
      assert not failed
    if observation_dict.get("failed") is not None:
      assert observation_dict["failed"] in [True, False]
      if observation_dict["failed"]:
        values = observation_dict.get("values", [])
        assert not values

  def __new__(cls, observation_dict):
    cls.validate_observation_dict(observation_dict)
    assignments = observation_dict["assignments"]
    values = []
    if observation_dict.get("values") is not None:
      values = [MetricEvaluation(**v) for v in observation_dict["values"]]
    failed = observation_dict.get("failed", False)
    task = []
    if observation_dict.get("task") is not None:
      task = LocalTask(**observation_dict["task"])
    observation = LocalObservation(
      assignments=LocalAssignments(assignments),
      values=values,
      failed=failed,
      task=task,
    )
    return observation
