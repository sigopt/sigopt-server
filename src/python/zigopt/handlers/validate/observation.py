# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
import json
from typing import Any

from zigopt.common import *
from zigopt.experiment.model import Experiment
from zigopt.handlers.validate.validate_dict import (
  ValidationType,
  get_opt_with_validation,
  key_present,
  validate_mutually_exclusive_properties,
)
from zigopt.handlers.validate.values import base_values_schema
from zigopt.net.errors import BadParamError
from zigopt.observation.model import Observation
from zigopt.task.from_json import extract_task_from_json

from libsigopt.aux.errors import MissingJsonKeyError
from libsigopt.aux.validate_schema import validate


observation_values_schema: dict[str, Any] = copy.deepcopy(base_values_schema)
observation_values_schema["items"]["required"] = ["value"]
observation_values_schema["type"] = ["array", "null"]
observation_values_schema["items"]["properties"]["name"] = {"type": ["string", "null"]}

observation_schema = {
  "additionalProperties": False,
  "properties": {
    "suggestion": {},
    "assignments": {},
    "values": observation_values_schema,
    "failed": {
      "type": ["boolean", "null"],
    },
    "no_optimize": {},
    "metadata": {
      "type": ["object", "null"],
    },
    "task": {
      "type": ["object", "string", "null"],
    },
  },
}


# NOTE: Much of the validation for task lies in extract_task_from_json but could be moved here
def validate_observation_json_dict_for_create(json_dict: dict[str, Any], experiment: Experiment) -> None:
  validate(json_dict, observation_schema)

  if get_opt_with_validation(json_dict, "failed", ValidationType.boolean) is True and json_dict.get("values"):
    raise BadParamError("Cannot provide `values` if observation has failed")

  validate_mutually_exclusive_properties(json_dict, ["suggestion", "assignments"])
  if not (key_present(json_dict, "suggestion") or key_present(json_dict, "assignments")):
    raise BadParamError(f"Must provide exactly one of `suggestion`, `assignments` in: {json.dumps(json_dict)}")

  if json_dict.get("failed") is not True:
    if json_dict.get("value") is None and not json_dict.get("values"):
      # TODO(SN-1195): when switching to mutli-values change this to error message to
      # ask for 'values' instead
      # TODO(RTL-107): Are we ever going to fully forbid value?  If not we might want to check the experiment
      # to return the correct error message
      raise MissingJsonKeyError("value", json_dict)

  if json_dict.get("values") is not None:
    if json_dict.get("value") is not None:
      raise BadParamError("Both 'value' and 'values' should not be specified.")
    if json_dict.get("value_stddev"):
      raise BadParamError("'value_stddev' should be specified within the 'values' list.")


def _get_assignments(json_dict, experiment, observation):
  if key_present(json_dict, "assignments"):
    return json_dict["assignments"]
  if not observation.processed_suggestion_id:
    return observation.get_assignments(experiment)
  return None


def _validate_task(json_dict, experiment):
  if not key_present(json_dict, "task"):
    return
  if not experiment.is_multitask:
    raise BadParamError("Only multitask experiments should have a task present.")
  if json_dict["task"] is not None:
    # This will error if the task is unacceptable
    extract_task_from_json(experiment, json_dict)


def validate_observation_json_dict_for_update(
  json_dict: dict[str, Any], experiment: Experiment, observation: Observation
) -> None:
  validate(json_dict, observation_schema)
  suggestion = json_dict["suggestion"] if key_present(json_dict, "suggestion") else observation.processed_suggestion_id

  assignments = _get_assignments(json_dict, experiment, observation)

  if (suggestion is not None and assignments is not None) or (suggestion is None and assignments is None):
    raise BadParamError("Must provide exactly one of `suggestion`, `assignments`")

  failed = json_dict["failed"] if key_present(json_dict, "failed") else observation.reported_failure
  if experiment.has_multiple_metrics:
    measurements = (
      json_dict["values"] if key_present(json_dict, "values") else observation.get_all_measurements(experiment)
    )
    if measurements is not None and failed is True:
      raise BadParamError("Multimetric observations with values cannot have failed == true")
    if measurements is None and failed is not True:
      raise BadParamError("Multimetric observations must either have values or failed == true")
  else:
    only_metric_name = experiment.all_metrics[0].name
    value = (
      json_dict["values"]
      if key_present(json_dict, "values")
      else json_dict["value"]
      if key_present(json_dict, "value")
      else observation.metric_value(experiment, only_metric_name)
    )

    if value is not None and failed is True:
      raise BadParamError("Observations with a value cannot have failed == true")
    if value is None and failed is not True:
      raise BadParamError("Observations must either have a value or failed == true")

  _validate_task(json_dict, experiment)
