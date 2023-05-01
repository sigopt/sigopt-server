# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.lib import BaseProxyClass, is_protobuf


class Proxy(BaseProxyClass):
  def __init__(self, underlying):
    if not is_protobuf(underlying):
      raise Exception("You can only create proxies from protobufs.")
    while isinstance(underlying, Proxy):
      underlying = underlying.underlying
    object.__setattr__(self, "underlying", underlying)

  def __getattr__(self, attr):
    return getattr(self.underlying, attr)

  def __eq__(self, other):
    raise TypeError("Cannot compare proxies")

  def __setattr__(self, attr, val):
    if attr in self.underlying.__class__.DESCRIPTOR.fields_by_name:
      # Calling setattr of a protobuf field on a Proxy is unlikely to behave the way the caller wants.
      # It appears to work but actually sets the value on the Proxy object instead of the underlying.
      # This is likely to cause confusion, so we forbid it.
      #
      # We could be more aggressive and forbid *any* setattr on a Proxy object - but
      # our codebase frequently sets cached values inside the constructor
      raise Exception(
        "Attempting to override value on underlying protobuf, which is not safe. Must call"
        " zigopt.protobuf.lib.copy_protobuf()"
      )
    return super().__setattr__(attr, val)

  def __ne__(self, other):
    raise TypeError("Cannot compare proxies")

  def __hash__(self):
    raise TypeError("Unhashable object")

  def __repr__(self):
    return f"{self.__class__.__name__}({repr(self.underlying)})"
