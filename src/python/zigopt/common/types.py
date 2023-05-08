# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# crosshair: on
import collections.abc
from typing import Any

import deal
import numpy

from zigopt.common.strings import is_serial


__all__ = ["is_iterable", "is_sequence", "is_mapping", "is_set"]


@deal.ensure(lambda val, result: result if isinstance(val, list) else True)
@deal.ensure(lambda val, result: result if isinstance(val, tuple) else True)
@deal.ensure(lambda val, result: result if isinstance(val, collections.abc.Generator) else True)
@deal.ensure(lambda val, result: result if isinstance(val, numpy.ndarray) else True)
@deal.ensure(lambda val, result: not result if isinstance(val, str) else True)
@deal.post(lambda result: isinstance(result, bool))
@deal.pure
def is_iterable(val: Any) -> bool:
  """
    Returns True iff this is an iterable type. Avoids the common error that strings
    and bytes are iterable.
    """
  return isinstance(val, collections.abc.Iterable) and not is_serial(val)


@deal.ensure(lambda val, result: result if isinstance(val, list) else True)
@deal.ensure(lambda val, result: result if isinstance(val, tuple) else True)
@deal.ensure(lambda val, result: result if isinstance(val, numpy.ndarray) else True)
@deal.ensure(lambda val, result: not result if isinstance(val, str) else True)
@deal.ensure(lambda val, result: not result if isinstance(val, collections.abc.Generator) else True)
@deal.post(lambda result: isinstance(result, bool))
@deal.pure
def is_sequence(val: Any) -> bool:
  """
    Returns True iff this is a "list-like" type. Avoids the common error that strings
    and bytes are iterable, and handles numpy and protobufs correctly
    """
  return (isinstance(val, collections.abc.Sequence) and not is_serial(val)) or isinstance(val, numpy.ndarray)


def is_mapping(val: Any) -> bool:
  """
    Returns True iff this is a "dict-like" type
    """
  return isinstance(val, collections.abc.Mapping)


def is_set(val: Any) -> bool:
  """
    Returns True iff this is a "set-like" type
    """
  return isinstance(val, collections.abc.Set)
