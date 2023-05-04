# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Callable, Optional, Sequence, TypeVar

import deal


T = TypeVar("T")


__all__ = ["find", "find_index"]


@deal.ensure(lambda lis, predicate, result: result in lis if any(predicate(v) for v in lis) else result is None)
@deal.raises(Exception)
def find(lis: Sequence[T], predicate: Callable[[T], bool]) -> Optional[T]:
  """
    Finds the first element in lis satisfying predicate, or else None
    """
  return next((item for item in lis if predicate(item)), None)


@deal.ensure(lambda lis, predicate, result: result < len(lis) if any(predicate(v) for v in lis) else result is None)
@deal.post(lambda result: result is None or result >= 0)
@deal.raises(Exception)
def find_index(lis: Sequence[T], predicate: Callable[[T], bool]) -> Optional[int]:
  """
    Finds the index of the first element in lis satisfying predicate, or else None
    """
  for index, item in enumerate(lis):
    if predicate(item):
      return index
  return None
