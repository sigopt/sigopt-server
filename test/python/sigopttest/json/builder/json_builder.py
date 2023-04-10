# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common import is_integer
from zigopt.json.builder import (
  InvalidFieldError,
  JsonBuilder,
  JsonBuilderValidationType,
  MissingFieldError,
  ValidationType,
  expose_fields,
  field,
)


class SimpleBuilder(JsonBuilder):
  object_name = "simple_builder"

  @field(ValidationType.boolean)
  def first(self):
    return True

  @field(ValidationType.boolean)
  def second(self):
    return False


class FieldTestObject(JsonBuilder):
  object_name = "field_test_object"

  @field(ValidationType.boolean, hide=lambda self: True)
  def hidden(self):
    raise Exception()

  @field(ValidationType.boolean, hide=lambda self: False)
  def visible(self):
    return True

  @field(ValidationType.boolean, field_name="right_name")
  def wrong_name(self):
    return True

  @field(ValidationType.boolean, field_name="second_visible", hide=lambda self: False)
  def returns_false(self):
    return False

  @expose_fields(
    fields=[
      ("exposed_field1", ValidationType.boolean),
      ("exposed_field2", ValidationType.boolean),
    ],
    getter=dict.get,
  )
  def returns_some_dict(self):
    return {
      "exposed_field1": False,
      "exposed_field2": True,
      "not_exposed_field": "unused",
    }


class EmptyBuilderTestObject(JsonBuilder):
  object_name = "empty_test_object"

  @expose_fields(fields=[], getter=lambda *_: pytest.fail("Should not get any attrs"))
  def returns_some_dict(self):
    return {
      "exposed_field1": False,
      "exposed_field2": True,
      "not_exposed_field": "unused",
    }


class BuilderTestObject(JsonBuilder):
  object_name = "builder_test_object"

  def __init__(self, data):
    self.data = data

  @field(ValidationType.none)
  def none(self):
    return self.data["none"]

  @field(ValidationType.boolean)
  def boolean(self):
    return self.data["boolean"]

  @field(ValidationType.integer)
  def integer(self):
    return self.data["integer"]

  @field(ValidationType.positive_integer)
  def positive_integer(self):
    return self.data["positive_integer"]

  @field(ValidationType.non_negative_integer)
  def non_negative_integer(self):
    return self.data["non_negative_integer"]

  @field(ValidationType.string)
  def string(self):
    return self.data["string"]

  @field(ValidationType.array)
  def array(self):
    return self.data["array"]

  @field(ValidationType.id)
  def id(self):
    return self.data["id"]

  @field(JsonBuilderValidationType())
  def json_builder_all_fields(self):
    return self.data["json_builder_all_fields"]

  @field(JsonBuilderValidationType(fields=["first"]))
  def json_builder_partial_fields(self):
    return self.data["json_builder_partial_fields"]


def instance_check(expected_type):
  def checker(value):
    assert isinstance(value, expected_type)

  return checker


def integer_check(value):
  assert is_integer(value)


class TestFieldsDecorator:
  @pytest.fixture
  def field_test_object(self):
    return FieldTestObject()

  def test_field_hidden(self, field_test_object):
    hidden_fields = field_test_object.resolve_fields(["hidden"])
    assert hidden_fields == {}

  def test_field_visible(self, field_test_object):
    visible_fields = field_test_object.resolve_fields(["visible"])
    assert visible_fields == {"visible": True}

  def test_named_field(self, field_test_object):
    named_fields = field_test_object.resolve_fields(["right_name"])
    assert named_fields == {"right_name": True}

  def test_exposed_field(self, field_test_object):
    exposed_fields = field_test_object.resolve_fields(["exposed_field1", "exposed_field2"])
    assert exposed_fields == {"exposed_field1": False, "exposed_field2": True}

  def test_not_exposed_field(self, field_test_object):
    with pytest.raises(MissingFieldError):
      field_test_object.resolve_fields(["not_exposed_field"])

  def test_empty_exposed_field(self):
    obj = EmptyBuilderTestObject()
    assert obj.resolve_all() == {"object": "empty_test_object"}

  def test_all_fields(self, field_test_object):
    all_fields = field_test_object.resolve_all()
    assert all_fields == {
      "visible": True,
      "right_name": True,
      "second_visible": False,
      "exposed_field1": False,
      "exposed_field2": True,
      "object": "field_test_object",
    }

  def test_missing_field(self, field_test_object):
    with pytest.raises(MissingFieldError):
      field_test_object.resolve_fields(["object", "not_a_field"])


class TestJsonBuilder:
  @pytest.mark.parametrize(
    "field,input_value,expected_value,checker",
    [
      ("none", None, None, instance_check(type(None))),
      ("boolean", False, False, instance_check(bool)),
      ("integer", -5, -5, integer_check),
      ("integer", 1, 1, integer_check),
      ("positive_integer", 1, 1, integer_check),
      ("non_negative_integer", 0, 0, integer_check),
      ("string", "hello", "hello", instance_check(str)),
      ("string", "hello", "hello", instance_check(str)),
      ("array", list(range(10)), list(range(10)), instance_check(list)),
      ("array", tuple(range(10)), list(range(10)), instance_check(list)),
      ("id", 42, "42", str),
      (
        "json_builder_all_fields",
        SimpleBuilder(),
        {"first": True, "second": False, "object": "simple_builder"},
        instance_check(dict),
      ),
      ("json_builder_partial_fields", SimpleBuilder(), {"first": True}, instance_check(dict)),
      ("object", None, "builder_test_object", str),
    ],
  )
  def test_valid_fields(self, field, input_value, expected_value, checker):
    output_json = BuilderTestObject({field: input_value}).resolve_fields([field])
    assert field in output_json
    assert {field: expected_value} == output_json
    checker(output_json[field])

  @pytest.mark.parametrize(
    "field,input_value",
    [
      ("none", 1),
      ("boolean", "false"),
      ("integer", "42"),
      ("positive_integer", -1),
      ("positive_integer", 0),
      ("non_negative_integer", -1),
      ("string", 1),
      ("array", "hello"),
      ("id", "42"),
      ("json_builder_all_fields", {}),
      ("json_builder_partial_fields", {}),
    ],
  )
  def test_invalid_fields(self, field, input_value):
    builder = BuilderTestObject({field: input_value})
    pytest.raises(InvalidFieldError, builder.resolve_fields, [field])

  def test_all_fields(self):
    input_json = {
      "none": None,
      "boolean": False,
      "integer": -5,
      "positive_integer": 1,
      "non_negative_integer": 0,
      "string": "hello",
      "array": list(range(10)),
      "id": 42,
      "json_builder_all_fields": SimpleBuilder(),
      "json_builder_partial_fields": SimpleBuilder(),
    }
    expected_json = {
      "none": None,
      "boolean": False,
      "integer": -5,
      "positive_integer": 1,
      "non_negative_integer": 0,
      "string": "hello",
      "array": list(range(10)),
      "id": "42",
      "json_builder_all_fields": {
        "first": True,
        "second": False,
        "object": "simple_builder",
      },
      "json_builder_partial_fields": {"first": True},
      "object": "builder_test_object",
    }
    assert expected_json == BuilderTestObject.json(input_json)
