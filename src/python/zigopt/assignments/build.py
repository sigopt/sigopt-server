# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.validate.assignments import get_assignment

from libsigopt.aux.errors import SigoptValidationError


def set_assignments_map_from_json(has_assignments_map, assignments_json, experiment):
  if assignments_json:
    for name, assignment_json in assignments_json.items():
      if name in experiment.conditionals_map:
        conditional = experiment.conditionals_map[name]
        # pylint: disable=cell-var-from-loop
        conditional_value = find(conditional.values, lambda c: c.name == assignment_json)
        # pylint: enable=cell-var-from-loop
        if conditional_value is None:
          raise SigoptValidationError(f"Invalid assignment {assignment_json} for conditional {conditional.name}")
        has_assignments_map.assignments_map[conditional.name] = conditional_value.enum_index
      elif name in experiment.all_parameters_map:
        parameter = experiment.all_parameters_map[name]
        assignment = get_assignment(parameter, assignment_json)
        has_assignments_map.assignments_map[parameter.name] = assignment
      else:
        raise SigoptValidationError(f'Invalid assignment, parameter does not exist: "{name}"')


def set_assignments_map_from_dict(has_assignments_map, assignments_map):
  for name, assignment in assignments_map.items():
    has_assignments_map.assignments_map[name] = assignment


def set_assignments_map_from_proxy(has_assignments_map, old_data, experiment):
  set_assignments_map_from_dict(has_assignments_map, old_data.get_assignments(experiment))


def set_assignments_map_with_conditionals_from_proxy(has_assignments_map, old_data, experiment):
  set_assignments_map_from_proxy(has_assignments_map, old_data, experiment)
  set_assignments_map_from_dict(has_assignments_map, old_data.get_assignments(experiment))
