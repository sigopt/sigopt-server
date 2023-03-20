# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.training_runs.list import STRING_TO_OPERATOR_DICT


FILTER_OPERATORS = list(STRING_TO_OPERATOR_DICT.keys())

run_view_schema = {
  "type": "object",
  "additionalProperties": False,
  "required": ["filters", "sort"],
  "properties": {
    "filters": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["operator", "field", "value", "enabled"],
        "properties": {
          "field": {"type": "string"},
          "operator": {"type": "string", "enum": FILTER_OPERATORS},
          "value": {"type": ["string", "number"]},
          "enabled": {"type": "boolean"},
        },
      },
    },
    "sort": {
      "type": "array",
      "minItems": 0,
      "maxItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["key", "ascending"],
        "properties": {
          "key": {"type": "string"},
          "ascending": {"type": "boolean"},
        },
      },
    },
    "column_state": {"type": "string"},
  },
}
