# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.api.errors import InvalidTypeError, InvalidValueError
from zigopt.api.validate_schema import validate


class TestValidateSchema(object):
  def test_validate_simple_array(self):
    schema = {
      "type": "array",
      "items": {
        "type": "object",
      },
    }
    with pytest.raises(InvalidTypeError):
      validate([{}, 2, {}], schema)
    with pytest.raises(InvalidTypeError):
      validate(["a"], schema)
    validate([], schema)

  def test_simply_nested_array(self):
    schema = {
      "type": "object",
      "properties": {
        "key_of_array": {
          "type": "array",
          "items": {
            "type": "string",
          },
        }
      },
    }
    with pytest.raises(InvalidTypeError):
      validate({"key_of_array": [1]}, schema)

  def test_deeply_nested_array(self):
    schema = {
      "type": "object",
      "properties": {
        "key_of_object": {
          "type": "object",
          "properties": {
            "key_of_array": {
              "type": "array",
              "items": {"type": "array", "items": {"type": "integer"}},
            }
          },
        }
      },
    }
    with pytest.raises(InvalidTypeError):
      validate({"key_of_object": {"key_of_array": [["a"]]}}, schema)

  def test_unspecific_index_error(self):
    schema = {"type": "array", "maxItems": 1}
    with pytest.raises(InvalidValueError):
      validate([{}, 2, {}], schema)

  def test_nested_unspecific_index_error(self):
    schema = {
      "type": "object",
      "properties": {"key_of_array": {"type": "array", "maxItems": 1}},
    }
    with pytest.raises(InvalidValueError):
      validate({"key_of_array": [{}, 2, {}]}, schema)
