# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import collections.abc
import numbers
from typing import Any

import numpy


__all__ = ["is_boolean", "is_integer", "is_integer_valued_number", "is_number", "is_nan"]


def is_boolean(x: Any) -> bool:
  return isinstance(x, bool)


def is_integer(num: Any) -> bool:
  """
    Returns True iff this is an integer type. Avoids the common error that bools
    are instances of int, and handles numpy correctly
    """
  if is_boolean(num):
    return False
  if isinstance(num, numbers.Integral):
    return True
  return False


def is_integer_valued_number(num: Any) -> bool:
  return is_number(num) and float(num).is_integer()


def is_number(x: Any) -> bool:
  if is_boolean(x):
    return False
  if isinstance(x, float) and not numpy.isfinite(x):
    return False
  return isinstance(x, numbers.Number) or is_integer(x)


def is_nan(x: Any) -> bool:
  """
    Safely checks if x can be handled by numpy.isnan before calling the function on x.
    Fixes issue where numpy.isnan fails when called with a python long value.
    """
  if isinstance(x, float):
    return numpy.isnan(x)
  if isinstance(x, collections.abc.Iterable):
    raise TypeError("zigopt.common.numbers.is_nan does not support iterables")
  return False
