# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from enum import Enum

from zigopt.assignments.build import set_assignments_map_from_json, set_assignments_map_from_proxy
from zigopt.handlers.validate.assignments import validate_assignments_map
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.protobuf.lib import copy_protobuf
from zigopt.task.from_json import extract_task_from_json

from libsigopt.aux.errors import InvalidValueError, SigoptValidationError


# This allows someone to pass just the task of a MT observation, not necessarily the assignments.
# Maybe should think if we actually want to allow that??
def set_observation_data_assignments_task_from_json(
  observation_data,
  observation,
  json_dict,
  experiment,
  suggestion,
):
  assignments_json = get_opt_with_validation(json_dict, "assignments", ValidationType.object)
  suggestion_json = get_opt_with_validation(json_dict, "suggestion", ValidationType.id)
  task_field_present = "task" in json_dict

  if suggestion_json is None and assignments_json is None:
    if experiment.is_multitask:
      raise SigoptValidationError(
        "Either `suggestion` or `assignments`+`task` must be provided when creating an observation"
      )
    raise SigoptValidationError("Must provide values for one of `suggestion` or `assignments`")
  if suggestion_json is not None and assignments_json is not None:
    raise SigoptValidationError("Cannot provide values for both `suggestion` and `assignments`")
  if suggestion_json is not None and assignments_json is None:
    if task_field_present:
      raise SigoptValidationError("Cannot provide/update `task` when `suggestion` is provided")
    set_observation_suggestion_from_json(observation_data, observation, suggestion_json, experiment, suggestion)
  else:
    set_observation_data_assignments_map_from_json(observation_data, json_dict, experiment)
    if experiment.is_multitask:
      if not task_field_present:
        raise SigoptValidationError("Must provide `assignments` and `task` when creating observations manually")
      set_observation_data_task_from_json(observation_data, json_dict, experiment)


def set_observation_suggestion_from_json(observation_data, observation, suggestion_json, experiment, suggestion):
  if suggestion is None or suggestion.experiment_id != experiment.id:
    raise InvalidValueError(f"No suggestion: {suggestion_json} for experiment: {experiment.id}")

  observation.processed_suggestion_id = suggestion.id
  observation_data.ClearField("assignments_map")
  set_assignments_map_from_proxy(observation_data, suggestion, experiment)

  if experiment.is_multitask:
    observation_data.task.CopyFrom(copy_protobuf(suggestion.task))


def set_observation_data_assignments_map_from_json(observation_data, json_dict, experiment):
  assignments_json = get_opt_with_validation(json_dict, "assignments", ValidationType.object)

  if not assignments_json:
    raise SigoptValidationError("Cannot provide null or empty `assignments`")

  observation_data.ClearField("assignments_map")
  set_assignments_map_from_json(observation_data, assignments_json, experiment)
  validate_assignments_map(observation_data.assignments_map, experiment)


def set_observation_data_task_from_json(observation_data, json_dict, experiment):
  task = extract_task_from_json(experiment, json_dict)
  if task:
    observation_data.task.CopyFrom(task)


class SuggestionAssignmentUpdates(Enum):
  NEITHER = 1
  BOTH = 2
  SUGGESTION_ONLY = 3
  ASSIGNMENTS_ONLY = 4


def _get_suggestion_assignments_update_type(update_suggestion: bool, update_assignments: bool):
  return (
    {
      (True, True): SuggestionAssignmentUpdates.BOTH,
      (True, False): SuggestionAssignmentUpdates.SUGGESTION_ONLY,
      (False, True): SuggestionAssignmentUpdates.ASSIGNMENTS_ONLY,
    }
  ).get((update_suggestion, update_assignments), SuggestionAssignmentUpdates.NEITHER)


def _check_suggestion_assignments_update(update, suggestion_json, assignments_json, observation):
  if update is SuggestionAssignmentUpdates.BOTH:
    if suggestion_json is None and assignments_json is None:
      raise SigoptValidationError("Cannot provide null for both `suggestion` and `assignments`")
    if suggestion_json is not None and assignments_json is not None:
      raise SigoptValidationError("Cannot set values for both `suggestion` and `assignments`")
    return
  if update is SuggestionAssignmentUpdates.SUGGESTION_ONLY:
    if observation.has_suggestion and suggestion_json is None:
      raise SigoptValidationError("Cannot provide null for `suggestion` without providing `assignments`")
    if not observation.has_suggestion and suggestion_json is not None:
      raise SigoptValidationError("Cannot provide `suggestion` without providing null for `assignments`")
    return
  if update is SuggestionAssignmentUpdates.ASSIGNMENTS_ONLY:
    if not observation.has_suggestion and assignments_json is None:
      raise SigoptValidationError("Cannot provide null for `assignments` without providing `suggestion`")
    if observation.has_suggestion and assignments_json is not None:
      raise SigoptValidationError("Cannot provide `assignments` without providing null not `suggestion`")
    return


def _check_task_update(json_dict, experiment, suggestion_json, assignments_json, observation):
  task_field_present = "task" in json_dict
  if experiment.is_multitask:
    observation_has_processed_suggestion = observation.processed_suggestion_id is not None
    if task_field_present:
      if assignments_json is None and json_dict["task"] is not None:
        if suggestion_json is None and observation_has_processed_suggestion:
          raise SigoptValidationError(
            "Cannot provide `task` for observation update for observation with associated suggestion"
          )
        if suggestion_json is not None:
          raise SigoptValidationError("Cannot provide `task` when updating observation to change associated suggestion")
    else:
      if observation_has_processed_suggestion and suggestion_json is None and assignments_json is not None:
        raise SigoptValidationError(
          "Most provide both `task` and `assignments` when updating observation to remove suggestion"
        )
  elif task_field_present:
    raise SigoptValidationError(f"Cannot provide `task` for experiment {experiment.id} which is not multitask")


def update_observation_data_assignments_task_from_json(
  observation_data,
  observation,
  json_dict,
  experiment,
  suggestion,
):
  assignments_json = get_opt_with_validation(json_dict, "assignments", ValidationType.object)
  suggestion_json = get_opt_with_validation(json_dict, "suggestion", ValidationType.id)

  update_suggestion = "suggestion" in json_dict
  update_assignments = "assignments" in json_dict

  update = _get_suggestion_assignments_update_type(update_suggestion, update_assignments)

  _check_suggestion_assignments_update(update, suggestion_json, assignments_json, observation)

  _check_task_update(json_dict, experiment, suggestion_json, assignments_json, observation)

  if suggestion_json is not None:
    if (
      update is SuggestionAssignmentUpdates.BOTH
      and assignments_json is None
      or update is SuggestionAssignmentUpdates.SUGGESTION_ONLY
      and observation.has_suggestion
    ):
      set_observation_suggestion_from_json(observation_data, observation, suggestion_json, experiment, suggestion)
  else:
    if assignments_json is not None:
      if (
        update is SuggestionAssignmentUpdates.BOTH
        and suggestion_json is None
        or update is SuggestionAssignmentUpdates.ASSIGNMENTS_ONLY
        and not observation.has_suggestion
      ):
        observation.processed_suggestion_id = None
        set_observation_data_assignments_map_from_json(
          observation_data,
          json_dict,
          experiment,
        )
    if "task" in json_dict:
      set_observation_data_task_from_json(observation_data, json_dict, experiment)
