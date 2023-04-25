# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, TypeVar

from google.protobuf.message import Message

from zigopt.common import *


MessageT = TypeVar("MessageT", bound=Message)


def get_field(proto: MessageT, name: str) -> Any:
  if name in proto.DESCRIPTOR.oneofs_by_name:
    raise ValueError(f"Cannot call GetFieldOrNone on oneof field: {name}")
  if proto.HasField(name):
    return getattr(proto, name)
  return None


def set_field(proto: MessageT, name: str, value: Any) -> None:
  # Ensure that we always raise on invalid attributes, even if value is None
  if not hasattr(proto, name):
    raise AttributeError(name)

  setattr(proto, name, value)


def get_oneof_value(proto: MessageT, name: str) -> None:
  which_oneof = proto.WhichOneof(name)
  if which_oneof is not None:
    return getattr(proto, which_oneof)
  return None


class BaseProxyClass:
  # Used to avoid cirucular import caused by is_protobuf and Proxy
  pass


def is_protobuf(val: Any) -> bool:
  return isinstance(val, (Message, BaseProxyClass))


def copy_protobuf(proto: MessageT) -> MessageT:
  copy = proto.__class__()
  copy.CopyFrom(proto)
  return copy
