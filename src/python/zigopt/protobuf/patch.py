# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

from google.protobuf.message import Message


def patch_protobuf_class(message_cls: type[Message]):
  original_setattr = message_cls.__setattr__

  def Message_setattr(self: Message, name: str, value: Any | None) -> None:
    if name in self.DESCRIPTOR.fields_by_name and value is None:
      return None
    return original_setattr(self, name, value)

  message_cls.__setattr__ = Message_setattr  # type: ignore
