# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from typing import Any, Callable

from zigopt.handlers.validate.color import color_hex_schema
from zigopt.tag.model import Tag

from libsigopt.aux.validate_schema import validate


tag_create_schema = {
  "type": "object",
  "required": ["name", "color"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": Tag.NAME_MAX_LENGTH,
    },
    "color": color_hex_schema,
  },
}


def validator(schema: dict[str, Any]) -> Callable[[dict[str, Any]], None]:
  schema = copy.deepcopy(schema)
  schema["additionalProperties"] = False

  def validate_json_dict(json_dict: dict[str, Any]) -> None:
    validate(json_dict, schema)

  return validate_json_dict


validate_tag_json_dict_for_create = validator(tag_create_schema)
