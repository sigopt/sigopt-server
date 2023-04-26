# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Generic, TypeVar

from google.protobuf.message import Message

from zigopt.common import *


MessageT = TypeVar("MessageT", bound=Message)


def get_oneof_value(proto: MessageT, name: str) -> Any:
  which_oneof = proto.WhichOneof(name)
  if which_oneof is not None:
    return getattr(proto, which_oneof)
  raise TypeError(f"No value set for oneof: {name}")


class BaseProxyClass(Generic[MessageT]):
  # Used to avoid cirucular import caused by is_protobuf and Proxy
  underlying: MessageT


def is_protobuf(val: Any) -> bool:
  return isinstance(val, (Message, BaseProxyClass))


def copy_protobuf(proto: MessageT | BaseProxyClass[MessageT]) -> MessageT:
  if isinstance(proto, BaseProxyClass):
    actual_proto = proto.underlying
  else:
    actual_proto = proto
  copy = actual_proto.__class__()
  copy.CopyFrom(actual_proto)
  return copy
