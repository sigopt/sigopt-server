# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, TypeVar

from google.protobuf.message import Message

from zigopt.common import *


MessageT = TypeVar("MessageT", bound=Message)


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
