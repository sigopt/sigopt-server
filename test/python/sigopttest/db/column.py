# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sqlalchemy import BigInteger, Column
from sqlalchemy.ext.declarative import declarative_base

from zigopt.db.column import *
from zigopt.protobuf.gen.test.message_pb2 import Child, Parent


Base: type = declarative_base()


class Model(Base):
  __tablename__ = "model"
  test_other_column = Column(BigInteger, primary_key=True)
  protobuf_column = ProtobufColumn(Parent)


class TestDbColumn:
  def access_path(self, path):
    clause = Model.protobuf_column
    for item in path:
      if isinstance(item, int):
        clause = clause[item]
      else:
        clause = getattr(clause, item)
    return clause

  @pytest.mark.parametrize(
    "path",
    [
      [],
      ["optional_double_field"],
      ["optional_string_field"],
      ["optional_composite_field", "name"],
      ["optional_composite_field", "value"],
      ["optional_recursive_field"],
      ["optional_recursive_field", "optional_double_field"],
      ["optional_recursive_field", "optional_recursive_field"],
      ["repeated_double_field"],
      ["repeated_double_field", 0],
      ["repeated_composite_field"],
      ["repeated_composite_field", 0],
      ["repeated_string_field"],
      ["repeated_string_field", 0],
      ["repeated_recursive_field"],
      ["repeated_recursive_field", 0],
      ["repeated_recursive_field", 0, "optional_double_field"],
      ["repeated_recursive_field", 0, "repeated_recursive_field"],
      ["repeated_recursive_field", 0, "repeated_recursive_field", 0],
      ["map_field"],
      ["recursive_map_field"],
    ],
  )
  def test_property_access(self, path):
    clause = self.access_path(path)
    assert unwind_json_path(clause) == path
    str(clause)

  def test_unwind_different_json_names(self):
    assert unwind_json_path(self.access_path(["variable_name"])) == ["serialized_name"]
    assert unwind_json_path(self.access_path(["optional_recursive_field", "variable_name"])) == [
      "optional_recursive_field",
      "serialized_name",
    ]

  def test_serialized_names(self):
    # pylint: disable=pointless-statement
    Model.protobuf_column.variable_name
    Model.protobuf_column["serialized_name"]
    Model.protobuf_column["variable_name"]
    with pytest.raises(AttributeError):
      Model.protobuf_column.serialized_name
    # pylint: enable=pointless-statement

  def test_mix_and_match(self):
    # pylint: disable=pointless-statement
    Model.protobuf_column.variable_recursive_field.variable_recursive_field.variable_name
    Model.protobuf_column.variable_recursive_field.variable_recursive_field["serialized_name"]
    Model.protobuf_column.variable_recursive_field["serialized_recursive_field"]["serialized_name"]
    Model.protobuf_column["serialized_recursive_field"]["serialized_recursive_field"]["serialized_name"]
    # pylint: enable=pointless-statement

  def test_invalid_mix_and_match(self):
    # pylint: disable=pointless-statement
    with pytest.raises(AttributeError):
      Model.protobuf_column.serialized_recursive_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.variable_recursive_field.typo_serialized_recursive_field
    with pytest.raises(AttributeError):
      Model.protobuf_column["serialized_recursive_field"]["serialized_recursive_field"].variable_name
    with pytest.raises(AttributeError):
      Model.protobuf_column.variable_recursive_field["serialized_recursive_field"].variable_recursive_field
    with pytest.raises(AttributeError):
      Model.protobuf_column["serialized_recursive_field"].variable_recursive_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.variable_recursive_field["serialized_recursive_field"].variable_name
    # pylint: enable=pointless-statement

  @pytest.mark.parametrize(
    "path",
    [
      [0],
      [""],
      ["something_fake"],
      ["optional_double_field", "too_far"],
      ["optional_double_field", 0],
      ["optional_composite_field", "something_fake"],
      ["optional_composite_field", 0],
      ["repeated_string_field", "something_fake"],
      ["repeated_composite_field", "value"],
      ["repeated_recursive_field", "repeated_recursive_field"],
      ["serialized_name"],
      ["variable_name", "serialized_name"],
    ],
  )
  def test_invalid_property_access(self, path):
    with pytest.raises((AttributeError, KeyError)):
      self.access_path(path)

  @pytest.mark.parametrize(
    "field",
    [
      "optional_double_field",
      "optional_string_field",
      "optional_composite_field",
      "optional_recursive_field",
      "variable_name",
    ],
  )
  def test_valid_fields(self, field):
    getattr(Model.protobuf_column, field)
    Model.protobuf_column.HasField(field)

  @pytest.mark.parametrize(
    "field",
    [
      "serialized_name",
      "fake_name",
    ],
  )
  def test_invalid_fields(self, field):
    with pytest.raises(AttributeError):
      getattr(Model.protobuf_column, field)
    with pytest.raises(AttributeError):
      Model.protobuf_column.HasField(field)

  def test_map_fields(self):
    # pylint: disable=pointless-statement
    Model.protobuf_column.recursive_map_field
    Model.protobuf_column.recursive_map_field["abc"]
    Model.protobuf_column.recursive_map_field["abc"].recursive_map_field
    Model.protobuf_column.recursive_map_field["abc"].recursive_map_field["def"]
    Model.protobuf_column.recursive_map_field["abc"].recursive_map_field["def"].optional_double_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.recursive_map_field.optional_double_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.recursive_map_field["abc"].fake_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.recursive_map_field["abc"].recursive_map_field.optional_double_field
    with pytest.raises(AttributeError):
      Model.protobuf_column.recursive_map_field["abc"].recursive_map_field["def"].fake_field
    # pylint: enable=pointless-statement

  @pytest.mark.parametrize(
    "base",
    [
      Model.protobuf_column,
      Model.protobuf_column.optional_double_field,
      Model.protobuf_column.optional_double_field.as_numeric(),
      Model.protobuf_column.optional_double_field.as_string(),
    ],
  )
  @pytest.mark.parametrize("op", ["is_", "isnot"])
  def test_is(self, base, op):
    with pytest.raises(NotImplementedError):
      getattr(base, op)(None)

  @pytest.mark.parametrize(
    "base",
    [
      Model.protobuf_column,
      Model.protobuf_column.optional_double_field,
    ],
  )
  def test_astext(self, base):
    # pylint: disable=pointless-statement
    with pytest.raises(NotImplementedError):
      base.astext
    # pylint: enable=pointless-statement

  @pytest.mark.parametrize(
    "path,expected",
    [
      ([], "{}"),
      (["a"], '{"a"}'),
      ([0], "{0}"),
      (["a", "b", "b"], '{"a","b","b"}'),
      (["a", 0, "c"], '{"a",0,"c"}'),
      ([0, 1, 2], "{0,1,2}"),
    ],
  )
  def test_json_path(self, path, expected):
    assert JsonPath(*path) == expected

  @pytest.mark.parametrize(
    "function",
    [
      jsonb_strip_nulls,
    ],
  )
  def test_generic_functions(self, function):
    name = function.__name__
    assert str(function()) == f"{name}()"
    assert str(function("a")) == f"{name}(:{name}_1)"

  def test_jsonb_set(self):
    assert (
      str(jsonb_set(Model.protobuf_column, JsonPath("value"), None))
      == "jsonb_set(model.protobuf_column,:jsonb_set_1,'null'::jsonb)"
    )
    assert (
      str(jsonb_set(Model.protobuf_column, JsonPath("value"), 1.1))
      == "jsonb_set(model.protobuf_column,:jsonb_set_1,:jsonb_set_2::jsonb)"
    )
    assert (
      str(jsonb_set(Model.protobuf_column, JsonPath("value"), Model.protobuf_column))
      == "jsonb_set(model.protobuf_column,:jsonb_set_1,coalesce(to_jsonb(model.protobuf_column),'null'))"
    )

  def test_invalid_jsonb_set(self):
    with pytest.raises(ValueError):
      jsonb_set()
    with pytest.raises(ValueError):
      jsonb_set(1, 2, 3, 4, 5)

  def test_adapt_for_jsonb(self):
    assert adapt_for_jsonb(True) == "true"
    assert adapt_for_jsonb(0) == "0"
    assert adapt_for_jsonb(1) == "1"
    assert adapt_for_jsonb("") == '""'
    assert adapt_for_jsonb("abc") == '"abc"'
    assert adapt_for_jsonb(0.0) == "0.0"
    assert adapt_for_jsonb(1.0) == "1.0"
    assert adapt_for_jsonb(coalesce({}, "null")) == coalesce("{}", "null")
    assert adapt_for_jsonb([1, 2, 3]) == "[1,2,3]"
    assert adapt_for_jsonb({}) == "{}"
    assert adapt_for_jsonb({"a": 1}) == '{"a":1}'
    assert adapt_for_jsonb({"a": []}) == '{"a":[]}'
    assert adapt_for_jsonb({"a": [0]}) == '{"a":[0]}'
    assert adapt_for_jsonb({"a": [1]}) == '{"a":[1]}'
    assert adapt_for_jsonb({"a": [1, 2]}) == '{"a":[1,2]}'
    assert adapt_for_jsonb({"a": [{}]}) == '{"a":[{}]}'
    assert adapt_for_jsonb({"a": {}}) == '{"a":{}}'
    assert adapt_for_jsonb({"a": {"b": 1}}) == '{"a":{"b":1}}'
    assert adapt_for_jsonb(Parent()) == "{}"
    assert adapt_for_jsonb(Parent(variable_name="a")) == '{"serialized_name":"a"}'
    assert (
      adapt_for_jsonb(Parent(optional_composite_field=Child(value=1.0))) == '{"optional_composite_field":{"value":1.0}}'
    )
    assert adapt_for_jsonb({"a": Parent()}) == '{"a":{}}'
