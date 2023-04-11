# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.handlers.validate.assignments import parameter_conditions_satisfied
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentConditional, ExperimentParameter


class BaseParamRenderException(Exception):
  pass


class ParamRenderException(BaseParamRenderException):
  def __init__(self, msg: str, parameter: ExperimentParameter, assignment: float):
    super().__init__(msg)
    self.parameter = parameter
    self.assignment = assignment


class ConditionalParamRenderException(BaseParamRenderException):
  def __init__(self, msg: str, conditional: ExperimentConditional, assignment: float):
    super().__init__(msg)
    self.conditional = conditional
    self.assignment = assignment


def render_param_value(parameter: ExperimentParameter, assignment: float) -> int | float | str:
  # categoricals are stored internally by their enum_index
  # so we reverse the mapping, from index back to name, for user-facing output
  try:
    if parameter.is_categorical:
      categorical_assignment = parameter.all_categorical_values_map_by_index.get(assignment)
      if categorical_assignment:
        return categorical_assignment.name
      raise ParamRenderException(f"Unknown categorical assignment, enum_index: {assignment}", parameter, assignment)
    if parameter.is_integer:
      return int(assignment)
    if parameter.is_double:
      return assignment
    raise ParamRenderException("Unknown parameter type", parameter, assignment)
  except ParamRenderException as e:
    raise ParamRenderException(
      f"Exception rendering assignment for parameter {parameter.name}: {e}", parameter, assignment
    ) from e


def render_conditional_value(conditional: ExperimentConditional, assignment: float) -> str:
  value = find(conditional.values, lambda c: c.enum_index == assignment)
  if value:
    return value.name
  raise ConditionalParamRenderException(
    f"Conditional {conditional.name} attempting to render unknown value {assignment}", conditional, assignment
  )


def conditionally_render_param_value(
  parameter: ExperimentParameter, assignment: float, assignments_dict: dict[str, float]
) -> Optional[int | float | str]:
  if parameter_conditions_satisfied(parameter, assignments_dict):
    return render_param_value(parameter, assignment)
  return None
