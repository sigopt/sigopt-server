# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Mapping

from zigopt.experiment.constraints import human_readable_constraint
from zigopt.experiment.model import Experiment, ExperimentParameterProxy
from zigopt.handlers.validate.validate_dict import ValidationType, validate_type
from zigopt.net.errors import BadParamError, ServerError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentConstraint, ExperimentParameter

from libsigopt.aux.constant import ConstraintType
from libsigopt.aux.errors import InvalidValueError


def get_assignment(param: ExperimentParameterProxy, assignment: float | str) -> float | str:
  """Return and validates a single assignment value of this parameter."""
  param = ExperimentParameterProxy(param)
  param_name = param.name

  if assignment is None:
    raise BadParamError(f"Missing assignment for parameter: {param_name}")

  if param.is_grid:
    if assignment not in param.grid_values:
      raise InvalidValueError(
        f"Invalid value for grid parameter {param_name}: {assignment}."
        f" Valid values for this parameter are: {param.grid_values}"
      )

  if param.is_categorical:
    validate_type(assignment, ValidationType.string, key=param_name)
    assignment_value = param.all_categorical_values_map.get(assignment)
    if assignment_value is None:
      raise InvalidValueError(
        f"Invalid value for categorical parameter {param_name}: {assignment}",
      )

    if assignment_value.deleted:
      raise BadParamError(
        f"Cannot report deleted categorical value {assignment} for parameter {param_name}",
      )

    return assignment_value.enum_index
  if param.is_integer:
    validate_type(assignment, ValidationType.integer, key=param_name)
  else:
    validate_type(assignment, ValidationType.number, key=param_name)
  return assignment


def parameter_conditions_satisfied(parameter: ExperimentParameterProxy, assignments_map: dict[str, Any]) -> bool:
  if parameter.conditions:
    for condition in parameter.conditions:
      assignment = assignments_map.get(condition.name)
      if assignment is not None and assignment not in condition.values:
        return False
  return True


def constraint_satisfied(constraint: ExperimentConstraint, assignments_map: dict[str, Any]) -> None:
  try:
    lhs = sum(term.coeff * assignments_map[term.name] for term in constraint.terms)
  except KeyError as e:
    raise BadParamError(f"Term {e.args[0]} is present in constraints, but no assignment was provided") from e

  if constraint.type == ConstraintType.greater_than:
    if not lhs >= constraint.rhs:
      raise BadParamError(f"Assignments do not satisfy constraint: {human_readable_constraint(constraint)}")
  elif constraint.type == ConstraintType.less_than:
    if not lhs <= constraint.rhs:
      raise BadParamError(f"Assignments do not satisfy constraint: {human_readable_constraint(constraint)}")
  else:
    raise ServerError(f"Cannot validate assignments for constraint type: {constraint.type}")


def transformation_satisfied(parameter: ExperimentParameter, assignment: float) -> None:
  if parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
    if assignment <= 0:
      raise BadParamError(f"Assignment must be positive for log-transformed parameter {parameter.name}")


def validate_assignments_map(assignments_map: Mapping[str, Any], experiment: Experiment) -> None:
  for conditional in experiment.conditionals:
    if conditional.name not in assignments_map:
      raise BadParamError(f'Missing assignment for conditional: "{conditional.name}"')

  for parameter in experiment.all_parameters:
    if parameter.name not in assignments_map:
      if parameter_conditions_satisfied(parameter, assignments_map):
        raise BadParamError(f'Missing assignment for parameter: "{parameter.name}"')
    else:
      if not parameter_conditions_satisfied(parameter, assignments_map):
        raise BadParamError(f'Do not provide assignment for unsatisfied parameter: "{parameter.name}"')

      assignment = assignments_map[parameter.name]
      transformation_satisfied(parameter, assignment)

  for constraint in experiment.constraints:
    constraint_satisfied(constraint, assignments_map)
