# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

from zigopt.handlers.validate.validate_dict import validate


note_schema = {
  "type": "object",
  "required": ["contents"],
  "additionalProperties": False,
  "properties": {
    "contents": {
      "type": "string",
      "maxLength": 1024 * 1024,  # 1MB if entirely ASCII
    },
  },
}


def validate_note_json_dict(json_dict: dict[str, Any]) -> None:
  validate(json_dict, note_schema)
