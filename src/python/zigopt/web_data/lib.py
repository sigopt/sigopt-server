# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.web_data.model import web_data_types_by_resource


# TODO(SN-1042): Move to common * list and add tests
def assert_keys_match(dict1, dict2, max_depth):
  def _compare_keys(d1, d2, max_depth, current_depth):
    if current_depth >= max_depth:
      return
    for key in d1:
      assert key in d2, f"Key: {key} has no match"
      if is_mapping(d1[key]):
        _compare_keys(d1[key], d2[key], max_depth, current_depth + 1)

  _compare_keys(dict1, dict2, max_depth, 0)
  _compare_keys(dict2, dict1, max_depth, 0)


# Ensure creators/validators/builders exist for each defined type.
def validate_web_data_dict(input_map, depth=2):
  parent_resources_map = {
    resource: {data_type: None for data_type in web_data_types}
    for resource, web_data_types in web_data_types_by_resource.items()
  }
  assert_keys_match(parent_resources_map, input_map, depth)
