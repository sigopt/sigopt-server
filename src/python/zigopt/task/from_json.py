# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.protobuf.lib import copy_protobuf

from libsigopt.aux.errors import InvalidKeyError, SigoptValidationError


def extract_task_from_json(experiment, json_dict):
  if not experiment.is_multitask:
    return None

  string_or_dict = ValidationType.oneOf([ValidationType.string, ValidationType.object])
  task_field = get_opt_with_validation(json_dict, "task", string_or_dict)
  if isinstance(task_field, dict):
    task_name = get_opt_with_validation(task_field, "name", ValidationType.string)
  else:
    task_name = task_field
  if task_name is None:
    raise InvalidKeyError("name", "A task name must be defined when creating suggestions for a multitask experiment.")

  try:
    task = experiment.get_task_by_name(task_name)
  except ValueError as e:
    raise SigoptValidationError(str(e)) from e

  return copy_protobuf(task)
