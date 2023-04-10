# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from google.protobuf.message import Message

from zigopt.common import *


# sigoptlint: disable=ProtobufMethodsRule


def CopyFrom(base, other):
  # NOTE: Soon this will be replaced with a safer implementat, but add a stub and lint rule
  # for now to make merging easier
  return base.CopyFrom(other)


def MergeFrom(base, other):
  # NOTE: Soon this will be replaced with a safer implementat, but add a stub and lint rule
  # for now to make merging easier
  return base.MergeFrom(other)


def GetFieldOrNone(underlying, name):
  if name in underlying.DESCRIPTOR.oneofs_by_name:
    raise ValueError(f"Cannot call GetFieldOrNone on oneof field: {name}")
  if underlying.HasField(name):
    return getattr(underlying, name)
  return None


def SetFieldIfNotNone(underlying, name, value):
  # Ensure that we always raise on invalid attributes, even if value is None
  if not hasattr(underlying, name):
    raise AttributeError(name)

  if value is not None:
    setattr(underlying, name, value)


def GetOneofValueOrNone(underlying, name):
  which_oneof = underlying.WhichOneof(name)
  if which_oneof is not None:
    return getattr(underlying, which_oneof)
  return None


class BaseProxyClass:
  # Used to avoid cirucular import caused by is_protobuf and Proxy
  pass


def is_protobuf(val):
  return isinstance(val, (Message, BaseProxyClass))
