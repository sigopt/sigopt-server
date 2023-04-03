# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.api.errors import InvalidTypeError, MissingJsonKeyError, SigoptValidationError
from zigopt.handlers.validate.validate_dict import (
  Base64InputValidator,
  Base64OutputValidator,
  ValidationType,
  get_with_validation,
  key_present,
  validate_mutually_exclusive_properties,
  validate_type,
)
from zigopt.protobuf.gen.color.color_pb2 import Color


class TestValidateType(object):
  def check_valid_validator(self, validator, value, expected):
    assert validate_type(value, validator) == expected

  def check_invalid_validator(self, validator, value):
    with pytest.raises(InvalidTypeError) as invalid_type_expected:
      validate_type(value, validator)
    invalid_type_error = invalid_type_expected.value
    assert invalid_type_error.value is value
    assert invalid_type_error.expected_type is validator

  @pytest.mark.parametrize(
    "value,expected",
    [
      (1, 1),
      (200000000000000000000, 200000000000000000000),
      ("3", 3),
      ("4", 4),
      (5.0, 5),
    ],
  )
  def test_valid_input_id(self, value, expected):
    self.check_valid_validator(ValidationType.id.get_input_validator(), value, expected)

  @pytest.mark.parametrize(
    "value",
    [
      "hello",
      "",
      {},
      [],
      1.2,
      "1.2",
    ],
  )
  def test_invalid_input_id(self, value):
    self.check_invalid_validator(ValidationType.id.get_input_validator(), value)

  @pytest.mark.parametrize(
    "value,expected",
    [
      (1, "1"),
      (2, "2"),
    ],
  )
  def test_valid_output_id(self, value, expected):
    self.check_valid_validator(ValidationType.id.get_output_validator(), value, expected)

  @pytest.mark.parametrize(
    "value",
    [
      "1",
      "2",
      "hello",
      "",
      {},
      [],
      1.2,
      "1.2",
    ],
  )
  def test_invalid_output_id(self, value):
    self.check_invalid_validator(ValidationType.id.get_output_validator(), value)

  @pytest.mark.parametrize(
    "value,expected",
    [
      ("1", 1),
      ("200000000000000000000", 200000000000000000000),
      ("-3", -3),
    ],
  )
  def test_valid_integer_string(self, value, expected):
    self.check_valid_validator(ValidationType.integer_string, value, expected)

  @pytest.mark.parametrize(
    "value",
    [
      "1e9",
      "not 200000000000000000000",
      "-3j",
      "4.0",
    ],
  )
  def test_invalid_integer_string(self, value):
    self.check_invalid_validator(ValidationType.integer_string, value)

  @pytest.mark.parametrize(
    "value",
    [
      "1",
      "200000000000000000000",
      "-3",
      "group",
      "hello7here",
      "_blank_",
      "-.---.----..",
    ],
  )
  def test_valid_id_string(self, value):
    self.check_valid_validator(ValidationType.id_string, value, value)

  @pytest.mark.parametrize(
    "value",
    [
      "",
      " ",
      "!hola!",
      "2+2=4-1=3",
      (8),
      (None),
    ],
  )
  def test_invalid_id_string(self, value):
    self.check_invalid_validator(ValidationType.id_string, value)

  @pytest.mark.parametrize(
    "value,expected",
    [
      ("", b""),
      ("aGVsbG8=", b"hello"),
      ("dGVzdA==", b"test"),
    ],
  )
  def test_valid_base64_input(self, value, expected):
    self.check_valid_validator(Base64InputValidator(len(expected)), value, expected)

  def test_invalid_base64_input_length(self):
    b64 = "aGVsbG8="  # base64 of "hello"
    self.check_invalid_validator(Base64InputValidator(4), b64)
    self.check_invalid_validator(Base64InputValidator(6), b64)

  @pytest.mark.parametrize(
    "value",
    [
      " ",
      "!hola!",
      "2+2=4-1=3",
      8,
      None,
      # substring is valid 4-length base64 (b64encoded "test")
      "dGVzdA==!@#$%^&*()_",
      "!@#$%^&*()_dGVzdA==",
      "dGVzdA==dGVzdA==",
      "\0",
      "😎",
    ],
  )
  def test_invalid_base64_input(self, value):
    self.check_invalid_validator(Base64InputValidator(4), value)

  @pytest.mark.parametrize(
    "value,expected",
    [
      (b"", ""),
      (
        b"hello",
        "aGVsbG8=",
      ),
      (
        b"test",
        "dGVzdA==",
      ),
    ],
  )
  def test_valid_base64_output(self, value, expected):
    self.check_valid_validator(Base64OutputValidator(len(value)), value, expected)

  def test_invalid_base64_output_length(self):
    self.check_invalid_validator(Base64OutputValidator(4), b"hello")
    self.check_invalid_validator(Base64OutputValidator(6), b"hello")

  @pytest.mark.parametrize(
    "value",
    [
      "application/octet-stream",
      "image/svg+xml",
      "text/plain",
    ],
  )
  def test_valid_mime_type(self, value):
    self.check_valid_validator(ValidationType.mime_type, value, value.lower())

  @pytest.mark.parametrize(
    "value",
    [
      "application",
      "svg+xml",
      "hello world",
      "\0/\0",
      "image/<>",
      "text/???",
      "hello/world",
      "image/",
      "image/ ",
      "image/\0",
      "image/\t",
    ],
  )
  def test_invalid_mime_type(self, value):
    self.check_invalid_validator(ValidationType.mime_type, value)

  @pytest.mark.parametrize(
    "color_hex,color_obj",
    [
      *(
        (
          "#" + l * 6,
          Color(red=int(l * 2, 16), green=int(l * 2, 16), blue=int(l * 2, 16)),
        )
        for l in ["0", "9", "a", "f", "A", "F"]
      ),
      ("#0a1B2c", Color(red=0x0A, green=0x1B, blue=0x2C)),
    ],
  )
  def test_valid_color_hex_input(self, color_hex, color_obj):
    self.check_valid_validator(ValidationType.color_hex.get_input_validator(), color_hex, color_obj)

  @pytest.mark.parametrize(
    "color_hex",
    [
      None,
      42,
      "",
      " ",
      "red",
      "RED",
      "!important",
      "#-1-1-1",
      *("#" + l * 6 for l in ("g", "G", "z", "Z")),
      "#-1-1-1",
      {"red": 0, "green": 0, "blue": 0},
      "#123456hellothere",
    ],
  )
  def test_invalid_color_hex_input(self, color_hex):
    self.check_invalid_validator(ValidationType.color_hex.get_input_validator(), color_hex)

  @pytest.mark.parametrize(
    "color_hex,color_obj",
    [
      *(
        (
          Color(red=int(l * 2, 16), green=int(l * 2, 16), blue=int(l * 2, 16)),
          "#" + l * 6,
        )
        for l in ["0", "9", "A", "F"]
      ),
      (Color(red=0x0A, green=0x1B, blue=0x2C), "#0a1B2c"),
    ],
  )
  def test_valid_color_hex_output(self, color_obj, color_hex):
    self.check_valid_validator(ValidationType.color_hex.get_input_validator(), color_obj, color_hex)


class TestGetWithValidation(object):
  @pytest.fixture
  def data(self):
    return {
      "points": [1.0, 2.0],
      "number": 3.141,
      "foo": "bar",
      "dict": dict(foo=12.3),
      "empty_dict": dict(),
      "string_id": "123",
      "int_id": 123,
      "invalid_id": "bad",
    }

  def test_valid_query(self, data):
    assert get_with_validation(data, "points", ValidationType.array) == [1.0, 2.0]
    assert get_with_validation(data, "points", ValidationType.arrayOf(ValidationType.number)) == [1.0, 2.0]
    assert get_with_validation(data, "dict", ValidationType.object) == {"foo": 12.3}
    assert get_with_validation(data, "empty_dict", ValidationType.object) == {}
    assert get_with_validation(data, "dict", ValidationType.objectOf(ValidationType.number)) == {"foo": 12.3}
    assert get_with_validation(data, "empty_dict", ValidationType.objectOf(ValidationType.number)) == {}
    assert get_with_validation(data, "number", ValidationType.number) == 3.141
    assert get_with_validation(data, "foo", ValidationType.string) == "bar"
    assert get_with_validation(data, "string_id", ValidationType.id) == 123
    assert get_with_validation(data, "int_id", ValidationType.id) == 123
    assert (
      get_with_validation(
        data,
        "int_id",
        ValidationType.oneOf([ValidationType.string, ValidationType.integer]),
      )
      == 123
    )
    assert (
      get_with_validation(
        data,
        "string_id",
        ValidationType.oneOf([ValidationType.string, ValidationType.integer]),
      )
      == "123"
    )

  def test_key_missing(self, data):
    key = "points"
    del data[key]
    with pytest.raises(MissingJsonKeyError) as missing_json_key:
      get_with_validation(data, key, None)
    assert missing_json_key.value.missing_json_key is key

  @pytest.mark.parametrize(
    "key,value_type",
    [
      ("number", ValidationType.string),
      ("points", ValidationType.object),
      ("string_id", ValidationType.array),
      ("number", ValidationType.integer),
      ("points", ValidationType.arrayOf(ValidationType.string)),
      ("number", ValidationType.oneOf([ValidationType.string, ValidationType.object])),
      ("dict", ValidationType.objectOf(ValidationType.string)),
    ],
  )
  def test_value_type_incorrect(self, data, key, value_type):
    with pytest.raises(InvalidTypeError) as type_error:
      get_with_validation(data, key, value_type)
    assert type_error.value.expected_type is value_type.get_input_validator()

  def test_transform_array_of(self):
    obj = {
      "list_of_numbers": [3, 4, 5],
      "list_of_strings": ["3", "4", "5"],
    }
    assert get_with_validation(obj, "list_of_numbers", ValidationType.arrayOf(ValidationType.number)) == [3, 4, 5]
    assert get_with_validation(obj, "list_of_strings", ValidationType.arrayOf(ValidationType.string)) == ["3", "4", "5"]
    assert get_with_validation(obj, "list_of_numbers", ValidationType.arrayOf(ValidationType.id)) == [3, 4, 5]
    assert get_with_validation(obj, "list_of_strings", ValidationType.arrayOf(ValidationType.id)) == [3, 4, 5]

  def test_transform_object_of(self):
    obj = {
      "dict_of_string_to_number": {"3": 1, "4": 2, "5": 3},
    }
    assert get_with_validation(
      obj,
      "dict_of_string_to_number",
      ValidationType.objectOf(ValidationType.number),
    ) == {"3": 1, "4": 2, "5": 3}
    assert get_with_validation(
      obj,
      "dict_of_string_to_number",
      ValidationType.objectOf(ValidationType.id),
    ) == {"3": 1, "4": 2, "5": 3}

  def test_invalid_id(self, data):
    key = "invalid_id"
    value_type = ValidationType.id
    with pytest.raises(InvalidTypeError):
      get_with_validation(data, key, value_type)

  @pytest.mark.parametrize(
    "string,value_type",
    [
      ("string", ValidationType.string),
      ("object", ValidationType.object),
      ("array", ValidationType.array),
      ("integer", ValidationType.integer),
      ("array[string]", ValidationType.arrayOf(ValidationType.string)),
      (
        "array[array[string]]",
        ValidationType.arrayOf(ValidationType.arrayOf(ValidationType.string)),
      ),
      ("oneOf[]", ValidationType.oneOf([])),
      ("string", ValidationType.oneOf([ValidationType.string])),
      (
        "oneOf[string, array[string]]",
        ValidationType.oneOf([ValidationType.string, ValidationType.arrayOf(ValidationType.string)]),
      ),
      (
        "array[oneOf[string, number, object]]",
        ValidationType.arrayOf(
          ValidationType.oneOf(
            [
              ValidationType.string,
              ValidationType.number,
              ValidationType.object,
            ]
          ),
        ),
      ),
      ("object<string, number>", ValidationType.objectOf(ValidationType.number)),
    ],
  )
  def test_str(self, string, value_type):
    assert str(value_type) == string


class TestValidateMutuallyExclusiveProperties(object):
  def test_only_validate_objects(self):
    with pytest.raises(InvalidTypeError):
      validate_mutually_exclusive_properties([], ["a", "b"])
    with pytest.raises(InvalidTypeError):
      validate_mutually_exclusive_properties(1, ["a", "b"])
    with pytest.raises(InvalidTypeError):
      validate_mutually_exclusive_properties("string", ["a", "b"])
    with pytest.raises(InvalidTypeError):
      validate_mutually_exclusive_properties(True, ["a", "b"])

  def test_empty_arguments(self):
    validate_mutually_exclusive_properties({}, [])

  def test_validation_succeeds(self):
    validate_mutually_exclusive_properties({}, ["a", "b"])
    validate_mutually_exclusive_properties({"c": 1}, ["a", "b"])
    validate_mutually_exclusive_properties({"a": 1}, ["a", "b"])
    validate_mutually_exclusive_properties({"b": 1, "c": 1}, ["a", "b"])
    validate_mutually_exclusive_properties({"a": 1}, [])

  def test_validation_fails(self):
    with pytest.raises(SigoptValidationError) as error:
      validate_mutually_exclusive_properties({"a": 1, "b": 1}, ["a", "b"])
    assert "`a`" in str(error.value) and "`b`" in str(error.value)

    with pytest.raises(SigoptValidationError) as error:
      validate_mutually_exclusive_properties({"a": 1, "b": 1, "c": 1}, ["a", "b"])
    assert "`a`" in str(error.value) and "`b`" in str(error.value) and "`c`" not in str(error.value)

  def test_key_present(self):
    assert key_present({"abc": "123"}, "abc")
    assert key_present({"abc": None}, "abc")
    assert not key_present({}, "abc")
    assert not key_present({"def": None}, "abc")

    with pytest.raises(TypeError) as error:
      key_present("abc", "def")
    assert str(error.value) == "Expected json_obj to be a mapping, received 'str'"
