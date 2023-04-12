# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError, SerializeToJsonError
from google.protobuf.message import Message
from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module


def _validate_class(fields: Sequence[FieldDescriptor]) -> None:
  seen_names = set([])
  for field in fields:
    serialize_name = field.json_name or field.name  # type: ignore
    if serialize_name in seen_names:
      raise ValueError(f"Unserializeable Protobuf message: duplicate name {serialize_name}")
    seen_names.add(serialize_name)


def protobuf_to_dict(obj: Message, **kwargs) -> dict:
  _validate_class(obj.DESCRIPTOR.fields)
  try:
    return MessageToDict(obj, **kwargs)
  except SerializeToJsonError as e:
    raise ValueError(e) from e


def dict_to_protobuf(Cls: type[Message], obj: dict, ignore_unknown_fields: bool = False) -> Message:
  _validate_class(Cls.DESCRIPTOR.fields)
  c = Cls()
  try:
    ParseDict(obj, c, ignore_unknown_fields=ignore_unknown_fields)
  except ParseError as e:
    raise ValueError(e) from e
  return c


def is_protobuf_struct_descriptor(descriptor: Descriptor) -> bool:
  assert isinstance(descriptor, Descriptor)
  return descriptor.full_name == "google.protobuf.Struct"


def is_protobuf_struct(obj: Message) -> bool:
  return isinstance(obj, Struct)


def dict_to_protobuf_struct(obj: dict) -> Struct:
  struct = dict_to_protobuf(Struct, obj)
  assert isinstance(struct, Struct)
  return struct


def protobuf_struct_to_dict(obj: Struct) -> dict:
  assert is_protobuf_struct(obj)
  return protobuf_to_dict(obj)
