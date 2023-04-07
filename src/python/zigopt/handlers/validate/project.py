# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from typing import Any, Callable

from zigopt.handlers.validate.validate_dict import ID_STRING_PATTERN
from zigopt.project.model import MAX_ID_LENGTH, MAX_NAME_LENGTH

from libsigopt.aux.validate_schema import validate


PROJECT_ID_SCHEMA = {
  "type": "string",
  "pattern": ID_STRING_PATTERN,
  "minLength": 1,
  "maxLength": MAX_ID_LENGTH,
}

project_create_schema = {
  "type": "object",
  "required": ["name", "id"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": MAX_NAME_LENGTH,
    },
    "id": PROJECT_ID_SCHEMA,
    "metadata": {
      "type": ["object", "null"],
    },
  },
}

project_update_schema = {
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": MAX_NAME_LENGTH,
    },
    "metadata": {
      "type": ["object", "null"],
    },
    "deleted": {
      "type": ["boolean", "null"],
    },
  },
}


def validator(schema: dict[str, Any]) -> Callable[[dict[str, Any]], None]:
  schema = copy.deepcopy(schema)
  schema["additionalProperties"] = False

  def validate_json_dict(json_dict: dict[str, Any]) -> None:
    validate(json_dict, schema)

  return validate_json_dict


validate_project_json_dict_for_create = validator(project_create_schema)
validate_project_json_dict_for_update = validator(project_update_schema)
