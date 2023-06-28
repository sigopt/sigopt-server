# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.protobuf.gen.test.message_pb2 import Child, Parent
from zigopt.protobuf.json import *


def _field_descriptor(field_name):
  return Parent.DESCRIPTOR.fields_by_name[field_name]


class TestUtils:
  def test_get_json_key(self):
    assert get_json_key(Parent.DESCRIPTOR, "optional_double_field") == float
    assert get_json_key(Parent.DESCRIPTOR, "optional_string_field") == str
    assert get_json_key(Parent.DESCRIPTOR, "optional_composite_field") == Child.DESCRIPTOR
    assert get_json_key(Parent.DESCRIPTOR, "optional_recursive_field") == Parent.DESCRIPTOR
    assert get_json_key(Parent.DESCRIPTOR, "repeated_double_field") == _field_descriptor("repeated_double_field")
    assert get_json_key(Parent.DESCRIPTOR, "repeated_string_field") == _field_descriptor("repeated_string_field")
    assert get_json_key(Parent.DESCRIPTOR, "repeated_composite_field") == _field_descriptor("repeated_composite_field")
    assert get_json_key(Parent.DESCRIPTOR, "repeated_recursive_field") == _field_descriptor("repeated_recursive_field")
    assert get_json_key(Parent.DESCRIPTOR, "map_field") == _field_descriptor("map_field")
    assert get_json_key(Parent.DESCRIPTOR, "recursive_map_field") == _field_descriptor("recursive_map_field")

    assert get_json_key(_field_descriptor("repeated_double_field"), 0) == float
    assert get_json_key(_field_descriptor("repeated_string_field"), 0) == str
    assert get_json_key(_field_descriptor("repeated_composite_field"), 0) == Child.DESCRIPTOR
    assert get_json_key(_field_descriptor("repeated_recursive_field"), 0) == Parent.DESCRIPTOR

  def test_invalid_get_json_key(self):
    with pytest.raises(AssertionError):
      get_json_key(float, "fake")
    with pytest.raises(AssertionError):
      get_json_key(str, "fake")
    with pytest.raises(InvalidPathError):
      get_json_key(Parent.DESCRIPTOR, "fake_name")

  def test_get_json_key_json_name(self):
    assert get_json_key(Parent.DESCRIPTOR, "variable_name", json=False) == str
    with pytest.raises(InvalidPathError):
      get_json_key(Parent.DESCRIPTOR, "variable_name", json=True)
    with pytest.raises(InvalidPathError):
      get_json_key(Parent.DESCRIPTOR, "serialized_name", json=False)
    assert get_json_key(Parent.DESCRIPTOR, "serialized_name", json=True) == str

    assert get_json_key(Parent.DESCRIPTOR, "variable_recursive_field", json=False) == Parent.DESCRIPTOR
    with pytest.raises(InvalidPathError):
      get_json_key(Parent.DESCRIPTOR, "variable_recursive_field", json=True)
    with pytest.raises(InvalidPathError):
      get_json_key(Parent.DESCRIPTOR, "serialized_recursive_field", json=False)
    assert get_json_key(Parent.DESCRIPTOR, "serialized_recursive_field", json=True) == Parent.DESCRIPTOR

  @pytest.mark.parametrize(
    "value, descriptor, eq",
    [
      (Parent(), Parent.DESCRIPTOR, {}),
      (Parent(optional_double_field=1.0), Parent.DESCRIPTOR, {"optional_double_field": 1.0}),
      (Parent(optional_string_field="a"), Parent.DESCRIPTOR, {"optional_string_field": "a"}),
      (Parent(optional_composite_field=Child()), Parent.DESCRIPTOR, {"optional_composite_field": {}}),
      (Parent(repeated_double_field=[1.0]), Parent.DESCRIPTOR, {"repeated_double_field": [1.0]}),
      (Parent(repeated_string_field=["a"]), Parent.DESCRIPTOR, {"repeated_string_field": ["a"]}),
      (Parent(repeated_composite_field=[Child()]), Parent.DESCRIPTOR, {"repeated_composite_field": [{}]}),
      (Parent(repeated_recursive_field=[Parent()]), Parent.DESCRIPTOR, {"repeated_recursive_field": [{}]}),
      (Parent(variable_name="a"), Parent.DESCRIPTOR, {"serialized_name": "a"}),
      (Parent(variable_recursive_field=Parent()), Parent.DESCRIPTOR, {"serialized_recursive_field": {}}),
      (1.0, _field_descriptor("optional_double_field"), 1.0),
      ("abc", _field_descriptor("optional_string_field"), "abc"),
      (Child(), _field_descriptor("optional_composite_field"), {}),
      (Child(name="a"), _field_descriptor("optional_composite_field"), {"name": "a"}),
      (Parent(), _field_descriptor("optional_recursive_field"), {}),
      (
        Parent(optional_double_field=1.0),
        _field_descriptor("optional_recursive_field"),
        {"optional_double_field": 1.0},
      ),
      ([1.0], _field_descriptor("repeated_double_field"), [1.0]),
      (["abc"], _field_descriptor("repeated_string_field"), ["abc"]),
      ([Child()], _field_descriptor("repeated_composite_field"), [{}]),
      ([Child(name="a")], _field_descriptor("repeated_composite_field"), [{"name": "a"}]),
      ([Parent()], _field_descriptor("repeated_recursive_field"), [{}]),
      (
        [Parent(optional_double_field=1.0)],
        _field_descriptor("repeated_recursive_field"),
        [{"optional_double_field": 1.0}],
      ),
      ({}, _field_descriptor("map_field"), {}),
      ({"a": 1.0}, _field_descriptor("map_field"), {"a": 1.0}),
      ({"a": 1.0, "b": 2.0}, _field_descriptor("map_field"), {"a": 1.0, "b": 2.0}),
      ({}, _field_descriptor("recursive_map_field"), {}),
      ({"a": Parent()}, _field_descriptor("recursive_map_field"), {"a": {}}),
      ({"a": Parent(), "b": Parent()}, _field_descriptor("recursive_map_field"), {"a": {}, "b": {}}),
      (
        {"a": Parent(optional_double_field=1.0)},
        _field_descriptor("recursive_map_field"),
        {"a": {"optional_double_field": 1.0}},
      ),
      (
        {"a": Parent(recursive_map_field={"b": Parent(optional_double_field=1.0)})},
        _field_descriptor("recursive_map_field"),
        {"a": {"recursive_map_field": {"b": {"optional_double_field": 1.0}}}},
      ),
    ],
  )
  def test_emit_json_with_descriptor(self, value, descriptor, eq):
    assert emit_json_with_descriptor(value, descriptor) == eq
    assert parse_json_with_descriptor(eq, descriptor, ignore_unknown_fields=True) == value

  @pytest.mark.parametrize(
    "value, descriptor",
    [
      (1.0, Parent.DESCRIPTOR),
      ("abc", Parent.DESCRIPTOR),
      ([1.0], Parent.DESCRIPTOR),
      (["abc"], Parent.DESCRIPTOR),
      ({}, Parent.DESCRIPTOR),
      ([], Parent.DESCRIPTOR),
      ([{}], Parent.DESCRIPTOR),
      (Parent(), _field_descriptor("optional_double_field")),
      ([1.0], _field_descriptor("optional_double_field")),
      ("abc", _field_descriptor("optional_double_field")),
      (1.0, _field_descriptor("optional_string_field")),
      (1.0, _field_descriptor("repeated_double_field")),
      (["abc"], _field_descriptor("repeated_double_field")),
      (Parent(), _field_descriptor("repeated_double_field")),
      ([Parent()], _field_descriptor("repeated_double_field")),
      ("abc", _field_descriptor("repeated_string_field")),
      ([1.0], _field_descriptor("repeated_string_field")),
      (Parent(), _field_descriptor("repeated_string_field")),
      ([Parent()], _field_descriptor("repeated_string_field")),
      (Parent(), _field_descriptor("repeated_recursive_field")),
      ([1.0], _field_descriptor("repeated_recursive_field")),
      (["abc"], _field_descriptor("repeated_recursive_field")),
      (1.0, _field_descriptor("map_field")),
      ([], _field_descriptor("map_field")),
      (["abc"], _field_descriptor("map_field")),
      ("abc", _field_descriptor("map_field")),
      (Parent(), _field_descriptor("map_field")),
      ([Parent()], _field_descriptor("map_field")),
      ({"a": Parent()}, _field_descriptor("map_field")),
      (1.0, _field_descriptor("recursive_map_field")),
      ([], _field_descriptor("recursive_map_field")),
      (["abc"], _field_descriptor("recursive_map_field")),
      ("abc", _field_descriptor("recursive_map_field")),
      (Parent(), _field_descriptor("recursive_map_field")),
      ([Parent()], _field_descriptor("recursive_map_field")),
      ({"a": 1.0}, _field_descriptor("recursive_map_field")),
    ],
  )
  def test_invalid_emit_json_with_descriptor(self, value, descriptor):
    with pytest.raises(ValueError):
      emit_json_with_descriptor(value, descriptor)

  @pytest.mark.parametrize(
    "value, descriptor",
    [
      (1.0, Parent.DESCRIPTOR),
      ("abc", Parent.DESCRIPTOR),
      ([1.0], Parent.DESCRIPTOR),
      (["abc"], Parent.DESCRIPTOR),
      (Parent(), Parent.DESCRIPTOR),
      ([], Parent.DESCRIPTOR),
      ([Parent()], Parent.DESCRIPTOR),
      ({}, _field_descriptor("optional_double_field")),
      ([1.0], _field_descriptor("optional_double_field")),
      ("abc", _field_descriptor("optional_double_field")),
      (1.0, _field_descriptor("optional_string_field")),
      (1.0, _field_descriptor("repeated_double_field")),
      (["abc"], _field_descriptor("repeated_double_field")),
      ({}, _field_descriptor("repeated_double_field")),
      ([{}], _field_descriptor("repeated_double_field")),
      ("abc", _field_descriptor("repeated_string_field")),
      ([1.0], _field_descriptor("repeated_string_field")),
      ({}, _field_descriptor("repeated_string_field")),
      ([{}], _field_descriptor("repeated_string_field")),
      ({}, _field_descriptor("repeated_recursive_field")),
      ([1.0], _field_descriptor("repeated_recursive_field")),
      (["abc"], _field_descriptor("repeated_recursive_field")),
      (1.0, _field_descriptor("map_field")),
      ([], _field_descriptor("map_field")),
      (["abc"], _field_descriptor("map_field")),
      ([1.0], _field_descriptor("map_field")),
      ("abc", _field_descriptor("map_field")),
      (Parent(), _field_descriptor("map_field")),
      ([Parent()], _field_descriptor("map_field")),
      ({"a": {}}, _field_descriptor("map_field")),
      (1.0, _field_descriptor("recursive_map_field")),
      ([], _field_descriptor("recursive_map_field")),
      (["abc"], _field_descriptor("recursive_map_field")),
      ([1.0], _field_descriptor("recursive_map_field")),
      ("abc", _field_descriptor("recursive_map_field")),
      (Parent(), _field_descriptor("recursive_map_field")),
      ([Parent()], _field_descriptor("recursive_map_field")),
      ({"a": 1.0}, _field_descriptor("recursive_map_field")),
    ],
  )
  def test_invalid_parse_json_with_descriptor(self, value, descriptor):
    with pytest.raises(ValueError):
      parse_json_with_descriptor(value, descriptor, ignore_unknown_fields=True)
