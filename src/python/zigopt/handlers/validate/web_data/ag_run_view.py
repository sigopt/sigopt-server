# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
column_state_schema = {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["colId"],
    "properties": {
      "colId": {"type": "string"},
      "width": {"type": "number"},
      "hide": {"type": "boolean"},
    },
  },
}

column_group_state_schema = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "groupId": {"type": "string"},
      "open": {"type": "boolean"},
    },
  },
}

sort_model_schema = {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["colId", "sort"],
    "additionalProperties": False,
    "properties": {
      "colId": {"type": "string"},
      "sort": {"type": "string", "enum": ["asc", "desc"]},
    },
  },
}

filter_model_schema = {"type": "object"}

ag_run_view_schema = {
  "type": "object",
  "additionalProperties": False,
  "required": ["columnState", "columnGroupState", "sortModel", "filterModel"],
  "properties": {
    "columnState": column_state_schema,
    "columnGroupState": column_group_state_schema,
    "sortModel": sort_model_schema,
    "filterModel": filter_model_schema,
  },
}
