# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Utils to check dicts and dict members arising from handler POST requests."""
import base64
import binascii
import enum
import json
import re
from typing import Any, Callable, Optional, Sequence

from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module
from jsonschema import validate as validate_against_schema  # type: ignore
from jsonschema.exceptions import ValidationError  # type: ignore

from zigopt.common import *
from zigopt.api.errors import (
  InvalidKeyError,
  InvalidTypeError,
  InvalidValueError,
  MissingJsonKeyError,
  RequestError,
  SigoptValidationError,
)
from zigopt.common.numbers import is_integer, is_integer_valued_number, is_number
from zigopt.protobuf.dict import (
  dict_to_protobuf,
  dict_to_protobuf_struct,
  is_protobuf_struct,
  protobuf_struct_to_dict,
  protobuf_to_dict,
)
from zigopt.protobuf.gen.color.color_pb2 import Color  # type: ignore
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import SysMetadata  # type: ignore


ID_STRING_PATTERN = r"^[a-z0-9\-_\.]+$"
ID_STRING_RE = re.compile(ID_STRING_PATTERN)


class IOValidatorInterface(object):
  def get_input_validator(self) -> "TypeValidatorBase":
    raise NotImplementedError()

  def get_output_validator(self) -> "TypeValidatorBase":
    raise NotImplementedError()


class TypeValidatorBase(IOValidatorInterface):
  def __init__(self, name: str):
    self.name = name

  def is_instance(self, obj: Any) -> bool:
    raise NotImplementedError()

  def transform(self, obj: Any) -> Any:
    raise NotImplementedError()

  def get_input_validator(self) -> "TypeValidatorBase":
    return self

  def get_output_validator(self) -> "TypeValidatorBase":
    return self

  def __str__(self) -> str:
    return self.name

  def __eq__(self, other: Any) -> bool:
    return self is other


class TypeValidator(TypeValidatorBase):
  def __init__(
    self,
    name: str,
    checker: Callable[[Any], bool],
    transformer: Optional[Callable[[Any], Any]] = None,
  ):
    super().__init__(name)
    self.checker = checker
    self.transformer = transformer or (identity)

  def is_instance(self, obj: Any) -> bool:
    return self.checker(obj)

  def transform(self, obj: Any) -> Any:
    return self.transformer(obj)

  def __eq__(self, other: Any) -> bool:
    return (
      other
      and self.__class__ == other.__class__
      and self.checker is other.checker
      and self.transformer is other.transformer
    )


identity_type_validator = TypeValidator("identity", lambda x: True)


class IOValidator(IOValidatorInterface):
  def __init__(
    self,
    name: str,
    input_validator: Optional[IOValidatorInterface] = None,
    output_validator: Optional[IOValidatorInterface] = None,
  ):
    self.name = name
    self.input_validator = identity_type_validator if input_validator is None else input_validator.get_input_validator()
    self.output_validator = (
      self.input_validator.get_output_validator()
      if output_validator is None
      else output_validator.get_output_validator()
    )

  def get_input_validator(self) -> TypeValidatorBase:
    return self.input_validator

  def get_output_validator(self) -> TypeValidatorBase:
    return self.output_validator

  def __str__(self) -> str:
    return self.name

  def __eq__(self, other: Any) -> bool:
    return (
      other
      and self.__class__ == other.__class__
      and self.get_input_validator() == other.get_input_validator()
      and self.get_output_validator() == other.get_output_validator()
    )

  def __ne__(self, other: Any) -> bool:
    return not self.__eq__(other)


class ArrayValidator(TypeValidator):
  def __init__(self, sub_validator: TypeValidatorBase):
    super().__init__(
      f"array[{str(sub_validator)}]",
      lambda xs: is_sequence(xs) and all(sub_validator.is_instance(x) for x in xs),
      lambda xs: [sub_validator.transform(x) for x in xs],
    )
    self.sub_validator = sub_validator

  def __eq__(self, other) -> bool:
    return other and self.__class__ == other.__class__ and self.sub_validator == other.sub_validator


class EnumValidator(TypeValidator):
  def __init__(self, enum: type[enum.Enum]):
    super().__init__(f"enum[{str(enum)}]", lambda xs: xs in list(enum.__members__))
    self.enum = enum

  def __eq__(self, other: Any) -> bool:
    return other and self.__class__ == other.__class__ and self.enum == other.enum


class OneOfTypeValidator(TypeValidatorBase):
  def __init__(self, validators: Sequence[TypeValidatorBase]):
    joined_validators = ", ".join(str(v) for v in validators)
    super().__init__(f"oneOf[{joined_validators}]")
    self.validators = validators

  def matching_validator(self, obj: Any) -> Optional[TypeValidatorBase]:
    return find(self.validators, lambda v: v.is_instance(obj))

  def is_instance(self, obj: Any) -> bool:
    return bool(self.matching_validator(obj))

  def transform(self, obj: Any) -> Any:
    v = self.matching_validator(obj)
    return v.transform(obj) if v else obj

  def __eq__(self, other: Any) -> bool:
    return other and self.__class__ == other.__class__ and self.validators == other.validators


class ObjectValidator(TypeValidator):
  def __init__(self, key_validator: TypeValidatorBase, value_validator: TypeValidatorBase):
    super().__init__(
      f"object<{key_validator}, {value_validator}>",
      lambda obj: (
        is_mapping(obj)
        and all(key_validator.is_instance(k) for k in obj.keys())
        and all(value_validator.is_instance(v) for v in obj.values())
      ),
      lambda obj: {key_validator.transform(k): value_validator.transform(v) for (k, v) in obj.items()},
    )
    self.key_validator = key_validator
    self.value_validator = value_validator

  def __eq__(self, other: Any) -> bool:
    return (
      other
      and self.__class__ == other.__class__
      and self.key_validator == other.key_validator
      and self.value_validator == other.value_validator
    )


class HexColorInputValidator(TypeValidatorBase):
  regex = re.compile(r"#" + r"([a-fA-F0-9]{2})" * 3)

  def __init__(self):
    super().__init__("input_color")

  def is_instance(self, obj: Any) -> bool:
    if not isinstance(obj, str):
      return False
    return bool(self.regex.fullmatch(obj))

  def transform(self, obj: Any) -> Color:
    match = self.regex.fullmatch(obj)
    assert match
    return Color(
      red=int(match.group(1), 16),
      green=int(match.group(2), 16),
      blue=int(match.group(3), 16),
    )


class HexColorOutputValidator(TypeValidatorBase):
  def __init__(self):
    super().__init__("output_color")

  def is_instance(self, obj: Any) -> bool:
    return isinstance(obj, Color)

  def transform(self, obj: Any) -> str:
    def int_to_hex(val):
      clamped = max(0, min(val, 255))
      return f"{clamped:02X}"

    return "".join(
      [
        "#",
        *(
          int_to_hex(val)
          for val in (
            obj.red,
            obj.green,
            obj.blue,
          )
        ),
      ]
    )


class Base64InputValidator(TypeValidatorBase):
  def __init__(self, length: int):
    super().__init__("input_base64")
    self.length = length

  def is_instance(self, obj: Any) -> bool:
    if isinstance(obj, str):
      try:
        decoded = base64.b64decode(obj, validate=True)
        return len(decoded) == self.length
      except (binascii.Error, ValueError):  # pylint: disable=c-extension-no-member
        pass
    return False

  def transform(self, obj: Any) -> bytes:
    return base64.b64decode(obj)


class Base64OutputValidator(TypeValidatorBase):
  def __init__(self, length: int):
    super().__init__("output_base64")
    self.length = length

  def is_instance(self, obj: Any) -> bool:
    return isinstance(obj, bytes) and len(obj) == self.length

  def transform(self, obj: Any) -> str:
    return base64.b64encode(obj).decode("ascii")


class MimeTypeValidator(TypeValidatorBase):
  VALID_BASE_TYPES = {
    "application",
    "audio",
    "font",
    "image",
    "message",
    "multipart",
    "text",
    "video",
  }

  # see definition of "token" in https://www.w3.org/Protocols/rfc1341/4_Content-Type.html
  PERMITTED_SUBTYPE_CHARS = set(chr(i) for i in range(33, 127)) - set(r"""()<>@,;:\"/[]?.=""")

  def __init__(self):
    super().__init__("mime_type")

  def split_type(self, obj: str) -> tuple[str, str]:
    base_type, sub_type = obj.split("/")
    return base_type.lower(), sub_type.lower()

  def is_valid_subtype(self, sub_type: str) -> bool:
    return len(sub_type) >= 1 and all(c in self.PERMITTED_SUBTYPE_CHARS for c in sub_type)

  def is_instance(self, obj: Any) -> bool:
    if not isinstance(obj, str):
      return False
    if not obj.count("/") == 1:
      return False
    base_type, sub_type = self.split_type(obj)
    if base_type not in self.VALID_BASE_TYPES:
      return False
    if not self.is_valid_subtype(sub_type):
      return False
    return True

  def transform(self, obj: Any) -> str:
    base_type, sub_type = self.split_type(obj)
    return f"{base_type}/{sub_type}"


def is_json(v: Any) -> bool:
  try:
    json.dumps(v)
    return True
  except (TypeError, ValueError):
    return False


class PrimitiveValidationType(object):
  object = TypeValidator("object", is_mapping)
  array = TypeValidator("array", is_sequence, list)
  string = TypeValidator("string", is_string, str)
  integer_string = TypeValidator("integer_string", lambda x: is_string(x) and not throws(ValueError, int, x), int)
  id_string = TypeValidator(
    "id_string",
    lambda x: is_string(x) and bool(ID_STRING_RE.fullmatch(x)),
  )
  boolean = TypeValidator("boolean", is_boolean)
  number = TypeValidator("number", is_number)
  json = TypeValidator("json", is_json)
  integer = TypeValidator("integer", is_integer_valued_number, int)
  positive_integer = TypeValidator("positive_integer", lambda x: is_integer_valued_number(x) and x > 0, int)
  non_negative_integer = TypeValidator("non_negative_integer", lambda x: is_integer_valued_number(x) and x >= 0, int)
  non_negative_number = TypeValidator("non_negative_number", lambda x: is_number(x) and x >= 0, float)
  none = TypeValidator("none", lambda x: x is None)
  mime_type = MimeTypeValidator()

  @classmethod
  def arrayOfPrimitive(cls, subvalidator: TypeValidatorBase) -> TypeValidatorBase:
    return ArrayValidator(subvalidator)

  @classmethod
  def oneOfPrimitive(cls, validators: Sequence[TypeValidatorBase]) -> TypeValidatorBase:
    if len(validators) == 1:
      return validators[0]
    return OneOfTypeValidator(validators)

  @classmethod
  def objectOfPrimitive(cls, value_validator: TypeValidatorBase) -> TypeValidatorBase:
    return ObjectValidator(ValidationType.string, value_validator)

  @classmethod
  def enum(cls, enum: type[enum.Enum]) -> EnumValidator:
    return EnumValidator(enum)


def create_array_io_validator(sub_validator: IOValidatorInterface) -> IOValidatorInterface:
  if isinstance(sub_validator, TypeValidatorBase):
    return PrimitiveValidationType.arrayOfPrimitive(sub_validator)
  return IOValidator(
    f"array[{str(sub_validator)}]",
    ArrayValidator(sub_validator.get_input_validator()),
    ArrayValidator(sub_validator.get_output_validator()),
  )


def create_one_of_type_io_validator(validators: Sequence[IOValidatorInterface]) -> IOValidatorInterface:
  if len(validators) == 1:
    return validators[0]
  joined_validators = ", ".join(str(e) for e in validators)
  return IOValidator(
    f"oneOf[{joined_validators}]",
    PrimitiveValidationType.oneOfPrimitive([v.get_input_validator() for v in validators]),
    PrimitiveValidationType.oneOfPrimitive([v.get_output_validator() for v in validators]),
  )


def create_object_io_validator(value_validator: IOValidatorInterface) -> IOValidatorInterface:
  vv = value_validator
  if isinstance(vv, TypeValidatorBase):
    return PrimitiveValidationType.objectOfPrimitive(vv)
  return IOValidator(
    f"object<string, {vv}>",
    PrimitiveValidationType.objectOfPrimitive(vv.get_input_validator()),
    PrimitiveValidationType.objectOfPrimitive(vv.get_output_validator()),
  )


# NOTE: numbers stored in protobuf Structs cannot be integers, but
# isinstance(json.loads("1"), int) and isinstance(json.loads("1.0"), float)
# so the python implementation of json does respect the difference.
# Ideally we would preserve this difference but it would require a fairly large change
# in the parsing and storing of metadata.
# So instead prefer rendering "1.0" as "1" which can be acheived by converting integral floats to int
# before serializing to json.
def metadata_output(pb_data: Struct) -> dict[str, Any]:
  dict_data = protobuf_struct_to_dict(pb_data)
  for k, v in dict_data.items():
    if isinstance(v, float) and v % 1 == 0:
      dict_data[k] = int(v)
  return dict_data


class ProtobufIOValidator(IOValidator):
  def __init__(self, name, Cls):
    def input_validate(x: Any) -> bool:
      if not isinstance(x, dict):
        return False
      try:
        dict_to_protobuf(Cls, x)
        return True
      except ValueError:
        return False

    def input_parse(x: Any) -> Cls:
      try:
        return dict_to_protobuf(Cls, x)
      except ValueError as e:
        raise ValueError(f"Parse {Cls} error: {e}") from e

    input_validator = TypeValidator(f"{name}Input", input_validate, input_parse)
    output_validator = TypeValidator(
      f"{name}Output", lambda x: isinstance(x, Cls), lambda x: protobuf_to_dict(x, preserving_proto_field_name=True)
    )
    super().__init__(name, input_validator, output_validator)


class ValidationType(PrimitiveValidationType):
  assignment = IOValidator(
    "assignment",
    PrimitiveValidationType.oneOfPrimitive((PrimitiveValidationType.string, PrimitiveValidationType.number)),
  )

  id = IOValidator(
    "id",
    PrimitiveValidationType.oneOfPrimitive((PrimitiveValidationType.integer_string, PrimitiveValidationType.integer)),
    TypeValidator("idOutput", is_integer, str),
  )

  metadata = IOValidator(
    "metadata",
    input_validator=TypeValidator("metadataInput", is_mapping, dict_to_protobuf_struct),
    output_validator=TypeValidator("metadataOutput", is_protobuf_struct, metadata_output),
  )

  sys_metadata = ProtobufIOValidator("sys_metadata", SysMetadata)

  color_hex = IOValidator(
    "color_hex",
    input_validator=HexColorInputValidator(),
    output_validator=HexColorOutputValidator(),
  )

  md5 = IOValidator("md5", input_validator=Base64InputValidator(16), output_validator=Base64OutputValidator(16))

  @classmethod
  def arrayOf(cls, subvalidator: IOValidatorInterface) -> IOValidatorInterface:
    return create_array_io_validator(subvalidator)

  @classmethod
  def oneOf(cls, validators: Sequence[IOValidatorInterface]) -> IOValidatorInterface:
    return create_one_of_type_io_validator(validators)

  @classmethod
  def objectOf(cls, value_validator: IOValidatorInterface) -> IOValidatorInterface:
    return create_object_io_validator(value_validator)

  @staticmethod
  def jsonschema_type_to_validation_type(schema: dict[str, Any], schema_type: Sequence | str) -> TypeValidatorBase:
    if is_sequence(schema_type):
      return ValidationType.oneOfPrimitive(
        [ValidationType.jsonschema_type_to_validation_type(schema, t) for t in schema_type]
      )
    assert isinstance(schema_type, str)
    if schema_type == "array":
      subschema = schema.get("items")
      if subschema and subschema.get("type"):
        return ValidationType.arrayOfPrimitive(
          ValidationType.jsonschema_type_to_validation_type(subschema, subschema["type"])
        )
      return ValidationType.array
    return {
      "integer": ValidationType.integer,
      "number": ValidationType.number,
      "string": ValidationType.string,
      "object": ValidationType.object,
      "boolean": ValidationType.boolean,
      "null": ValidationType.none,
    }[schema_type]


def validate_type(value: Any, value_type: TypeValidatorBase, key: Optional[str] = None) -> Any:
  """
    Return ``value`` if the data is of the type ``value_type``.
    Prefer this to isinstance.
    """
  if value_type.is_instance(value):
    return value_type.transform(value)
  else:
    raise InvalidTypeError(value, value_type, key=key)


def key_present(json_obj: dict[str, Any], key: str) -> bool:
  if not is_mapping(json_obj):
    raise TypeError(f"Expected json_obj to be a mapping, received '{type(json_obj).__name__}'")
  return key in json_obj


def get_opt_with_validation(json_obj: dict[str, Any], key: str, value_type: IOValidatorInterface) -> Any:
  """
    Return json_obj[key] if the data is "safe".

    :param json_obj: a dict that may or may not contain ```key```
    :type json: dict
    :param key: key to check in input
    :type key: any (typically str; should be cleanly repr'd)
    :param value_type: expected type for ``json_obj[key]``
    :type value_type: type
    :return: ``json_obj[key]``
    :rtype: ``value_type`` or None

    """
  value = json_obj.get(key)
  if value is None:
    return None
  return validate_type(value, value_type.get_input_validator(), key=key)


def get_unvalidated(json_obj: dict[str, Any], key: str) -> Any:
  value = json_obj.get(key)
  if value is None:
    raise MissingJsonKeyError(key, json_obj)
  return value


def get_with_validation(json_obj: dict[str, Any], key: str, value_type: IOValidatorInterface) -> Any:
  """
    Return json_obj[key] if the data is "safe".

    Check that ``key`` is in ``json_obj`` and the type of ``json_obj[key]`` is ``value_type``.

    :param json_obj: a dict that may or may not contain ```key```
    :type json: dict
    :param key: key to check in input
    :type key: any (typically str; should be cleanly repr'd)
    :param value_type: expected type for ```json_obj[key]``
    :type value_type: type
    :return: ``json_obj[key]``
    :rtype: ``value_type``

    """
  value = get_unvalidated(json_obj, key)
  return validate_type(value, value_type.get_input_validator(), key=key)


def validate_mutually_exclusive_properties(json_dict: dict[str, Any], properties: Sequence[str]) -> None:
  """
    At most one of properties can be present in json_dict
    """
  validate_type(json_dict, ValidationType.object)
  present = [p for p in properties if json_dict.get(p) is not None]
  if len(present) > 1:
    present_str = " and ".join(f"`{p}`" for p in present)
    raise SigoptValidationError(f"Cannot specify {present_str}.")


def validate(json_dict: dict[str, Any], schema: dict[str, Any]) -> None:
  try:
    validate_against_schema(json_dict, schema)
  except ValidationError as e:
    raise process_error(e) from e


def get_path_string(path: Sequence[int | str]) -> str:
  strings = (f"[{part}]" if is_integer(part) else f".{part}" for part in path)
  return "".join(strings)


def process_error(e: ValidationError) -> RequestError:
  if e.validator == "additionalProperties" and e.validator_value is False:
    unknown_keys = re.findall(r"u?'(\w+)',?", e.message)
    unknown_keys_str = ", ".join([f"`{p}`" for p in unknown_keys])
    msg = f"Unknown json keys {unknown_keys_str} in: {json.dumps(e.instance)}"
    invalid_key = unknown_keys[0] if len(unknown_keys) > 0 else None
    return InvalidKeyError(invalid_key, msg)
  elif e.validator == "type":
    validation_type = ValidationType.jsonschema_type_to_validation_type(e.schema, e.schema["type"])
    return InvalidTypeError(e.instance, validation_type, key=get_path_string(e.path))
  elif e.validator in ["maxProperties", "minProperties"]:
    least_most = "at least" if e.validator == "minProperties" else "at most"
    return SigoptValidationError(f"Expected {least_most} {e.validator_value} keys in {json.dumps(e.instance)}")
  elif e.validator == "required":
    if is_mapping(e.instance):
      missing_keys = [key for key in e.validator_value if key not in e.instance]
      missing_key = missing_keys[0] if len(missing_keys) > 0 else None
    else:
      missing_key = e.validator_value[0]
    return MissingJsonKeyError(missing_key, e.instance)
  elif e.validator in ["minimum", "maximum"]:
    key = get_path_string(e.path)
    greater_less = "greater than" if e.validator == "minimum" else "less than"
    return InvalidValueError(f"{key} must be {greater_less} or equal to {e.validator_value}")
  elif e.validator in ["minLength", "maxLength", "minItems", "maxItems"]:
    key = get_path_string(e.path)
    greater_less = "greater than" if e.validator in ["minLength", "minItems"] else "less than"
    return InvalidValueError(f"The length of {key} must be {greater_less} or equal to {e.validator_value}")
  elif e.validator == "enum":
    allowed_values = ", ".join([str(s) for s in e.validator_value if s is not None])
    return SigoptValidationError(f"{e.instance} is not one of the allowed values: {allowed_values}")
  elif e.validator == "pattern":
    return SigoptValidationError(f"{e.instance} does not match the regular expression /{e.validator_value}/")
  elif e.validator in ["oneOf", "anyOf"]:
    if len(e.context) > 0:
      return process_error(e.context[0])
    return NotImplementedError("Error has no context but it is oneOf or anyOf")
  else:
    return NotImplementedError(f"Unrecognized error {e.validator} parsing json: {json.dumps(e.instance)}")
