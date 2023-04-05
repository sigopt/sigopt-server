# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from typing import Any

from zigopt.handlers.validate.experiment import experiment_create_schema, experiment_update_schema

from libsigopt.aux.validate_schema import validate


ai_experiment_create_schema: dict[str, Any] = copy.deepcopy(experiment_create_schema)
ai_experiment_update_schema: dict[str, Any] = copy.deepcopy(experiment_update_schema)
for key in (
  "metric",
  "observation_budget",
  "project",
  "runs_only",
  "tasks",
):
  ai_experiment_create_schema["properties"].pop(key, None)
  ai_experiment_update_schema["properties"].pop(key, None)

# disallow shorthand metric names
for schema in (ai_experiment_create_schema, ai_experiment_update_schema):
  schema["properties"]["metrics"]["items"]["type"] = ["object"]


def validate_ai_experiment_json_dict_for_create(json_dict: dict[str, Any]) -> None:
  schema = copy.deepcopy(ai_experiment_create_schema)
  schema["additionalProperties"] = False
  validate(json_dict, schema)


def validate_ai_experiment_json_dict_for_update(json_dict: dict[str, Any]):
  schema = copy.deepcopy(ai_experiment_update_schema)
  schema["additionalProperties"] = False
  validate(json_dict, schema)
