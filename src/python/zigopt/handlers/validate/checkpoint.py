# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from typing import Any

from zigopt.common import *
from zigopt.handlers.validate.validate_dict import validate
from zigopt.handlers.validate.values import base_values_schema


checkpoint_values_schema: dict[str, Any] = copy.deepcopy(base_values_schema)
checkpoint_values_schema["items"]["required"] = ["value", "name"]
checkpoint_values_schema["type"] = ["array"]
checkpoint_values_schema["items"]["properties"]["name"] = {"type": ["string"]}

checkpoint_schema = {
  "additionalProperties": False,
  "required": ["values"],
  "properties": {
    "values": checkpoint_values_schema,
    "metadata": {
      "type": ["object", "null"],
    },
  },
}


def validate_checkpoint_json_dict_for_create(json_dict: dict[str, Any]) -> None:
  validate(json_dict, checkpoint_schema)
