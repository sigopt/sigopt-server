# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.protobuf.lib import GetFieldOrNone, GetOneofValueOrNone, SetFieldIfNotNone


# sigoptlint: disable=ProtobufMethodsRule
def patch_protobuf_class(Message):
  def _copy_protobuf(self):
    copy = self.__class__()
    copy.CopyFrom(self)
    return copy

  Message.GetFieldOrNone = GetFieldOrNone
  Message.GetOneofValueOrNone = GetOneofValueOrNone
  Message.SetFieldIfNotNone = SetFieldIfNotNone
  Message.copy_protobuf = _copy_protobuf
