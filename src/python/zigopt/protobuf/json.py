# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.json_format import _IsMapEntry as IsMapEntry  # type: ignore
from google.protobuf.message_factory import GetMessageClass  # type: ignore

from zigopt.common import *
from zigopt.protobuf.dict import dict_to_protobuf, is_protobuf_struct_descriptor, protobuf_to_dict
from zigopt.protobuf.lib import is_protobuf


class InvalidPathError(ValueError):
  pass


_NO_ARG = object()


class ZigoptDescriptor:
  python_type: type

  def __call__(self, *args, **kwargs):
    raise NotImplementedError

  def serialize(self, value):
    raise NotImplementedError


class OurEnumDescriptor(ZigoptDescriptor):
  python_type = int

  def __init__(self, descriptor):
    self.descriptor = descriptor

  def __call__(self, serialized_value=_NO_ARG):
    if serialized_value is _NO_ARG:
      return self.descriptor.default_value
    assert is_string(serialized_value)
    enum_value = self.descriptor.enum_type.values_by_name.get(serialized_value)
    if enum_value is None:
      raise ValueError(f"Unknown name for enum {self.descriptor.enum_type.name}: {serialized_value}")
    return enum_value.number

  def serialize(self, value):
    serialized_value = self.descriptor.enum_type.values_by_number.get(value)
    if serialized_value is None:
      raise ValueError(f"Unknown number for enum {self.descriptor.enum_type.name}: {value}")
    return serialized_value.name


class DescriptorWithDefault(ZigoptDescriptor):
  def __init__(self, type_, default):
    self.python_type = type_
    self.default_value = default

  def __call__(self):
    return self.python_type(self.default_value)

  def serialize(self, value):
    return self.python_type(value)


def next_descriptor_for_field_descriptor(descriptor):
  if descriptor.message_type is not None:
    return descriptor.message_type
  if descriptor.type == FieldDescriptor.TYPE_ENUM:
    return OurEnumDescriptor(descriptor)

  python_type = (
    {
      FieldDescriptor.TYPE_BOOL: bool,
      FieldDescriptor.TYPE_DOUBLE: float,
      FieldDescriptor.TYPE_FIXED32: int,
      FieldDescriptor.TYPE_FIXED64: int,
      FieldDescriptor.TYPE_FLOAT: float,
      FieldDescriptor.TYPE_INT32: int,
      FieldDescriptor.TYPE_INT64: int,
      FieldDescriptor.TYPE_SFIXED32: int,
      FieldDescriptor.TYPE_SFIXED64: int,
      FieldDescriptor.TYPE_SINT32: int,
      FieldDescriptor.TYPE_SINT64: int,
      FieldDescriptor.TYPE_STRING: str,
      FieldDescriptor.TYPE_UINT32: int,
      FieldDescriptor.TYPE_UINT64: int,
    }
  ).get(descriptor.type)
  if python_type is None:
    raise NotImplementedError(f"Unknown message type: {descriptor.type}")
  return python_type


def field_descriptor_to_scalar_descriptor(field_descriptor):
  if field_descriptor.message_type:
    raise NotImplementedError("message types are not supported in this function")
  python_type = next_descriptor_for_field_descriptor(field_descriptor)
  if field_descriptor.has_default_value:
    return DescriptorWithDefault(python_type, field_descriptor.default_value)
  return python_type


def get_json_key_from_field_descriptor(descriptor, key):
  assert isinstance(descriptor, FieldDescriptor)
  is_array_access = is_integer(key)
  if is_array_access:
    if descriptor.label != FieldDescriptor.LABEL_REPEATED:
      raise InvalidPathError(f"{key} is not a repeated field for {descriptor.full_name}")
    reached_end = descriptor.message_type is None
    if reached_end:
      return field_descriptor_to_scalar_descriptor(descriptor)
    return descriptor.message_type
  if descriptor.label == FieldDescriptor.LABEL_REPEATED:
    if IsMapEntry(descriptor):
      value_field = descriptor.message_type.fields_by_name["value"]
      return next_descriptor_for_field_descriptor(value_field)
    raise InvalidPathError(f"{key} is a repeated field for {descriptor.full_name}")
  raise TypeError("Did not dereference FieldDescriptor message_type")


def get_json_key(descriptor, key, json=False):
  assert hasattr(descriptor, "GetOptions"), "validate_path can only be called on protobuf descriptors"
  assert descriptor is not None

  is_field_descriptor = isinstance(descriptor, FieldDescriptor)
  is_array_access = is_integer(key)
  if is_field_descriptor:
    descriptor = get_json_key_from_field_descriptor(descriptor, key)
  else:
    if is_array_access:
      raise InvalidPathError(f"{key} is not a repeated field for {descriptor.full_name}")
    for field in descriptor.fields:
      accessor_name = field.name
      if json:
        assert field.json_name
        accessor_name = field.json_name
      if accessor_name == key:
        descriptor = field
        if descriptor.label != FieldDescriptor.LABEL_REPEATED:
          if descriptor.type == FieldDescriptor.TYPE_MESSAGE:
            descriptor = descriptor.message_type
          else:
            descriptor = field_descriptor_to_scalar_descriptor(descriptor)
        break
    else:
      raise InvalidPathError(f"Invalid attribute for {descriptor}: {key}")
  assert descriptor is not None
  return descriptor


def _validate_array(value, descriptor, is_emit):
  if isinstance(descriptor, FieldDescriptor):
    is_repeated_field = (descriptor.label == FieldDescriptor.LABEL_REPEATED) and not IsMapEntry(descriptor)
    is_array = is_sequence(value)
    if is_array ^ is_repeated_field:
      raise ValueError("Expected repeated field descriptor for array values")
    return is_array
  return False


def is_valid_field_descriptor_for_value(value, descriptor, is_emit):
  if descriptor.type == FieldDescriptor.TYPE_MESSAGE:
    return is_protobuf(value) if is_emit else is_mapping(value)
  return is_valid_scalar_descriptor_for_value(
    value,
    next_descriptor_for_field_descriptor(descriptor),
  )


def is_valid_scalar_descriptor_for_value(value, descriptor):
  try:
    return descriptor(value) == value
  except (TypeError, ValueError):
    return False


def emit_json_with_descriptor(value, descriptor):
  # pylint: disable=too-many-return-statements
  is_array = _validate_array(value, descriptor, is_emit=True)
  if is_array:
    next_descriptor = next_descriptor_for_field_descriptor(descriptor)
    return [emit_json_with_descriptor(v, next_descriptor) for v in value]
  if isinstance(descriptor, Descriptor):
    if is_protobuf_struct_descriptor(descriptor):
      if is_mapping(value):
        return value
    elif is_protobuf(value):
      return protobuf_to_dict(value)
    raise ValueError(f"Invalid value for protobuf descriptor {descriptor.full_name}: {value}")
  if isinstance(descriptor, FieldDescriptor):
    if IsMapEntry(descriptor):
      if is_mapping(value):
        value_field = descriptor.message_type.fields_by_name["value"]
        next_descriptor = next_descriptor_for_field_descriptor(value_field)
        return map_dict(lambda v: emit_json_with_descriptor(v, next_descriptor), value)
      raise ValueError(f"Unknown map type: {type(value)}")
    if is_valid_field_descriptor_for_value(value, descriptor, is_emit=True):
      return protobuf_to_dict(value) if is_protobuf(value) else value
    raise ValueError(f"Invalid value for field descriptor {descriptor.full_name}: {value}")
  if isinstance(descriptor, ZigoptDescriptor):
    return descriptor.serialize(value)
  if is_valid_scalar_descriptor_for_value(value, descriptor):
    return value
  raise ValueError(f"Invalid value for scalar descriptor {descriptor}: {value}")


def parse_json_with_descriptor(value, descriptor, ignore_unknown_fields):
  # pylint: disable=too-many-return-statements
  is_array = _validate_array(value, descriptor, is_emit=False)
  if is_array:
    next_descriptor = next_descriptor_for_field_descriptor(descriptor)
    return [parse_json_with_descriptor(v, next_descriptor, ignore_unknown_fields) for v in value]
  if isinstance(descriptor, Descriptor):
    if is_mapping(value):
      Cls = GetMessageClass(descriptor)
      return dict_to_protobuf(Cls, value, ignore_unknown_fields=ignore_unknown_fields)
    raise ValueError(f"Invalid value for protobuf descriptor {descriptor.full_name}: {value}")
  if isinstance(descriptor, FieldDescriptor):
    if IsMapEntry(descriptor):
      if is_mapping(value):
        value_field = descriptor.message_type.fields_by_name["value"]
        next_descriptor = next_descriptor_for_field_descriptor(value_field)
        return map_dict(
          lambda v: parse_json_with_descriptor(v, next_descriptor, ignore_unknown_fields),
          value,
        )
      raise ValueError(f"Invalid value for map descriptor {descriptor.full_name}: {value}")
    if is_valid_field_descriptor_for_value(value, descriptor, is_emit=False):
      if is_mapping(value):
        Cls = GetMessageClass(descriptor.message_type)
        return dict_to_protobuf(Cls, value, ignore_unknown_fields=ignore_unknown_fields)
      return value
    raise ValueError(f"Invalid value for field descriptor {descriptor.full_name}: {value}")
  if isinstance(descriptor, OurEnumDescriptor):
    return descriptor(value)
  if is_valid_scalar_descriptor_for_value(value, descriptor):
    return value
  raise ValueError(f"Invalid value for scalar descriptor {descriptor}: {value}")
