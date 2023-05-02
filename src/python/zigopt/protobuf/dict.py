# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# crosshair: on
from typing import Sequence, TypeVar

import deal
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


@deal.raises(ValueError)
@deal.has()
def protobuf_to_dict(obj: Message, **kwargs) -> dict:
  _validate_class(obj.DESCRIPTOR.fields)
  try:
    return MessageToDict(obj, **kwargs)
  except SerializeToJsonError as e:
    raise ValueError(e) from e


ProtobufType = TypeVar("ProtobufType", bound=Message)


@deal.raises(ValueError)
@deal.has()
def dict_to_protobuf(Cls: type[ProtobufType], obj: dict, ignore_unknown_fields: bool = False) -> ProtobufType:
  _validate_class(Cls.DESCRIPTOR.fields)
  c = Cls()
  try:
    ParseDict(obj, c, ignore_unknown_fields=ignore_unknown_fields)
  except ParseError as e:
    raise ValueError(e) from e
  return c


@deal.pre(lambda descriptor: isinstance(descriptor, Descriptor))
@deal.pure
def is_protobuf_struct_descriptor(descriptor: Descriptor) -> bool:
  return descriptor.full_name == "google.protobuf.Struct"


@deal.pre(lambda obj: isinstance(obj, Message))
@deal.pure
def is_protobuf_struct(obj: Message) -> bool:
  return isinstance(obj, Struct)


@deal.post(lambda result: isinstance(result, Struct))
@deal.pure
def dict_to_protobuf_struct(obj: dict) -> Struct:
  # crosshair: off
  return dict_to_protobuf(Struct, obj)


@deal.pre(lambda obj: isinstance(obj, Struct))
@deal.pure
def protobuf_struct_to_dict(obj: Struct) -> dict:
  return protobuf_to_dict(obj)
