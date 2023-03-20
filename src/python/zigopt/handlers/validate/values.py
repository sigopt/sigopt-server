# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# NOTE: Used by checkpoints and regular observations, only make changes here if you want it to apply to both
base_values_schema = {
  "items": {
    "type": ["object"],
    "additionalProperties": False,
    "properties": {
      "value": {
        "type": ["number"],
      },
      "value_stddev": {
        "type": ["number", "null"],
        "minimum": 0.0,
      },
    },
  }
}
