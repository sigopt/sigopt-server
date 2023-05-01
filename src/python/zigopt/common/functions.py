# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Callable, Optional, TypeVar


T = TypeVar("T")
G = TypeVar("G")

__all__ = ["identity", "napply", "throws"]


def identity(obj: T) -> T:
  """
    Returns obj
    """
  return obj


def napply(obj: Optional[T], func: Callable[[T], G]) -> Optional[G]:
  """
    Applies the function if obj is not None.
    """
  if obj is not None:
    return func(obj)
  return None


def throws(exc: type[BaseException], func: Callable, *args, **kwargs) -> bool:
  """
    Checks if the function throws the exception.
    Does not catch other exceptions.
    """
  try:
    func(*args, **kwargs)
    return False
  except exc:
    return True
