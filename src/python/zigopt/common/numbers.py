# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import collections.abc as _collectionsabc
import numbers as _numbers
from typing import Any as _Any

import numpy as _numpy


def is_boolean(x: _Any) -> bool:
  return isinstance(x, bool)


def is_integer(num: _Any) -> bool:
  """
    Returns True iff this is an integer type. Avoids the common error that bools
    are instances of int, and handles numpy correctly
    """
  if is_boolean(num):
    return False
  elif isinstance(num, _numbers.Integral):
    return True
  else:
    return False


def is_integer_valued_number(num: _Any) -> bool:
  return is_number(num) and float(num).is_integer()


def is_number(x: _Any) -> bool:
  if is_boolean(x):
    return False
  if isinstance(x, float) and not _numpy.isfinite(x):
    return False
  return isinstance(x, _numbers.Number) or is_integer(x)


def is_nan(x: _Any) -> bool:
  """
    Safely checks if x can be handled by numpy.isnan before calling the function on x.
    Fixes issue where numpy.isnan fails when called with a python long value.
    """
  if isinstance(x, float):
    return _numpy.isnan(x)
  elif isinstance(x, _collectionsabc.Iterable):
    raise TypeError("zigopt.common.numbers.is_nan does not support iterables")
  else:
    return False
