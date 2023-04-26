# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

from google.protobuf.descriptor import Descriptor
from google.protobuf.message import Message


def patch_protobuf_class(message_cls: type[Message]):
  original_getattribute = message_cls.__getattribute__
  original_setattr = message_cls.__setattr__

  def Message_getattribute(self: object, name: str) -> Any | None:
    descriptor: Descriptor = original_getattribute(self, "DESCRIPTOR")
    if name not in descriptor.fields_by_name:
      return original_getattribute(self, name)
    if name in descriptor.oneofs_by_name:
      raise ValueError(f"Cannot call GetFieldOrNone on oneof field: {name}")
    has_field = original_getattribute(self, "HasField")
    if has_field(name):
      return original_getattribute(self, name)
    return None

  def Message_setattr(self: object, name: str, value: Any | None) -> None:
    # Ensure that we always raise on invalid attributes, even if value is None
    if not hasattr(self, name):
      raise AttributeError(name)

    if value is None:
      delattr(self, name)
    else:
      original_setattr(self, name, value)

  message_cls.__getattribute__ = Message_getattribute  # type: ignore
  message_cls.__setattr__ = Message_setattr  # type: ignore
