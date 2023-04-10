# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.validate.experiment import validate_conditional_value
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.net.errors import BadParamError
from zigopt.parameters.from_json import set_parameter_name_from_json

from libsigopt.aux.errors import InvalidValueError


def set_experiment_conditionals_list_from_json(experiment_meta, experiment_json):
  conditionals_json = get_opt_with_validation(
    experiment_json,
    "conditionals",
    ValidationType.arrayOf(ValidationType.object),
  )

  if not conditionals_json:
    return

  seen_names = set()
  for conditional_json in conditionals_json:
    conditional = experiment_meta.conditionals.add()
    set_conditional_from_json(conditional, conditional_json)

    if conditional.name in seen_names:
      raise BadParamError(f"Duplicate conditional name {conditional.name}")
    seen_names.add(conditional.name)


def set_conditional_from_json(conditional, conditional_json):
  set_conditional_name_from_json(conditional, conditional_json)
  set_conditional_values_from_json(conditional, conditional_json)


def set_conditional_name_from_json(conditional, conditional_json):
  set_parameter_name_from_json(conditional, conditional_json)


def set_conditional_values_from_json(conditional, conditional_json):
  conditional_values_json = get_with_validation(
    conditional_json,
    "values",
    ValidationType.arrayOf(ValidationType.string),
  )

  seen_values = set()
  for enum_index, conditional_value_json in enumerate(conditional_values_json or [], start=1):
    conditional_value = conditional.values.add()
    conditional_value.enum_index = enum_index
    conditional_value.name = validate_conditional_value(conditional_value_json)

    if conditional_value.name in seen_values:
      raise InvalidValueError(
        f"Duplicate conditional value {conditional_value.name} for conditional named {conditional.name}"
      )
    seen_values.add(conditional_value.name)

  if not conditional.values:
    raise BadParamError(f"No values provided for conditional {conditional.name}")
  if len(conditional.values) < 2:
    raise BadParamError(f"Conditional {conditional.name} must have at least 2 values")
