# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""
Like collections.namedtuple, but safer.

collections.namedtuple, unfortunately, generates subclasses of `tuple`. This means
that it is easy to accidentally treat objects as iterable collections when you do
not mean to.

This class prevents that error by being stricter about which features are available.
The generated class can only be used to get and set fields by name.
"""

import collections


FORBIDDEN_FIELDS = (
  "__getitem__",
  "__getslice__",
  "__iter__",
  "__len__",
  "__getnewargs__",
  "__getstate__",
  "count",
  "index",
)


def ImmutableStruct(name, args, defaults=None):
  fields = tuple(args)
  assert defaults is None or len(defaults) == len(fields)
  underlying_cls = collections.namedtuple(name, fields, defaults=defaults)

  class StructClass:
    def __init__(self, *args, **kwargs):
      underlying = underlying_cls(*args, **kwargs)
      assert isinstance(underlying, tuple)
      self._underlying = underlying

    def __getattr__(self, attr):
      if attr in FORBIDDEN_FIELDS:
        raise AttributeError(attr)
      underlying = object.__getattribute__(self, "_underlying")
      return getattr(underlying, attr)

    def __getinitargs__(self):
      return self._underlying.__getinitargs__()

    def __repr__(self):
      return repr(self._underlying)

    def __hash__(self):
      return hash(self._underlying)

    def __eq__(self, other):
      # pylint: disable=protected-access
      return self.__class__ == other.__class__ and self._underlying == other._underlying
      # pylint: enable=protected-access

    def __ne__(self, other):
      return not self.__eq__(other)

  StructClass.__name__ = name
  StructClass._fields = fields
  return StructClass
