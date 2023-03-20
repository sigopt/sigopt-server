# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.assignments.build import set_assignments_map_from_json
from zigopt.handlers.validate.assignments import validate_assignments_map
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.task.from_json import extract_task_from_json


def build_suggestion_data_from_json(experiment, json_dict):
  suggestion_data = SuggestionData(task=extract_task_from_json(experiment, json_dict))
  set_assignments_map_from_json(
    has_assignments_map=suggestion_data,
    assignments_json=get_opt_with_validation(json_dict, "assignments", ValidationType.object),
    experiment=experiment,
  )
  validate_assignments_map(suggestion_data.assignments_map, experiment)
  return suggestion_data
