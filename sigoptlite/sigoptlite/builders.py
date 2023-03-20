# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from sigoptaux.constant import (
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MAX_NUM_INT_CONSTRAINT_VARIABLES,
  ConstraintType,
  ParameterTransformationNames,
)
from sigoptaux.geometry_utils import find_interior_point
from sigoptlite.models import (
  LocalAssignments,
  LocalExperiment,
  LocalObservation,
  LocalTask,
  MetricEvaluation,
  dataclass_to_dict,
)


def create_experiment_from_template(experiment_template, **kwargs):
  experiment_meta = dataclass_to_dict(experiment_template)
  experiment_meta.update(kwargs)
  return LocalExperimentBuilder(experiment_meta)


class LocalExperimentBuilder(object):
  cls_name = "sigoptlite experiment"

  def __new__(cls, experiment_meta):
    cls.validate_experiment_meta(experiment_meta)
    experiment = LocalExperiment(**experiment_meta)
    cls.validate_experiment_object(experiment)
    return experiment

  @classmethod
  def validate_experiment_meta(cls, experiment_meta):
    assert len(experiment_meta["parameters"]) > 0
    assert len(experiment_meta["metrics"]) > 0

  @classmethod
  def validate_experiment_object(cls, experiment):
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

    # Check feature viability of multisolution experiments
    num_solutions = experiment.num_solutions
    if num_solutions and num_solutions > 1:
      if num_solutions > observation_budget:
        raise ValueError("observation_budget needs to be larger than the number of solutions")
      if not len(experiment.optimized_metrics) == 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions require exactly one optimized metric")

    # Check feature viability of multitask
    tasks = experiment.tasks
    if tasks:
      if experiment.requires_pareto_frontier_optimization:
        raise ValueError(f"{cls.cls_name} cannot have both tasks and multiple optimized metrics")
      if experiment.has_constraint_metrics:
        raise ValueError(f"{cls.cls_name} cannot have both tasks and constraint metrics")
      if num_solutions and num_solutions > 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions cannot be multitask")

    # Check conditional limitation
    if experiment.is_conditional:
      if num_solutions and num_solutions > 1:
        raise ValueError(f"{cls.cls_name} with multiple solutions does not support conditional parameters")
      if experiment.is_search:
        raise ValueError(f"All-Constraint {cls.cls_name} does not support conditional parameters")

    if experiment.linear_constraints:
      cls.validate_constraints(experiment)
      cls.check_constraint_feasibility(experiment)

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
