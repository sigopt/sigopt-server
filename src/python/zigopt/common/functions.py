# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Callable as _Callable
from typing import Optional as _Optional
from typing import TypeVar as _TypeVar


T = _TypeVar("T")
G = _TypeVar("G")


def identity(obj: T) -> T:
  """
    Returns obj
    """
  return obj


def napply(obj: _Optional[T], func: _Callable[[T], G]) -> _Optional[G]:
  """
    Applies the function if obj is not None.
    """
  if obj is not None:
    return func(obj)
  return None


def throws(exc: type[BaseException], func: _Callable, *args, **kwargs) -> bool:
  """
    Checks if the function throws the exception.
    Does not catch other exceptions.
    """
  try:
    func(*args, **kwargs)
    return False
  except exc:
    return True
