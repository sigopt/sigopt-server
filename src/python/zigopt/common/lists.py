# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""
Common utility functions for working with lists
"""
# crosshair: on
import collections
import enum
import itertools
from typing import TYPE_CHECKING, Any, Callable, Collection, Hashable, Iterable, Iterator, Optional, Sequence, TypeVar

import deal

from zigopt.common.functions import identity
from zigopt.common.generators import unsafe_generator
from zigopt.common.types import is_iterable


if TYPE_CHECKING:
  import _typeshed

  type_Comparable = _typeshed.SupportsRichComparison


T = TypeVar("T")
THashable = TypeVar("THashable", bound=Hashable)

__all__ = [
  "flatten",
  "coalesce",
  "partition",
  "distinct",
  "distinct_by",
  "max_option",
  "min_option",
  "list_get",
  "tail",
  "chunked",
  "sliding",
  "as_tuple",
]


class Sentinel(enum.Enum):
  NO_ARG = 0


@deal.pre(lambda lis: all(isinstance(v, collections.abc.Collection) for v in lis))
@deal.ensure(lambda lis, result: all(item in result for seq in lis for item in seq))
def flatten(lis: Sequence[Collection[T]]) -> list[T]:
  """
    :param lis: A list of iterables
    Returns a list comprised of the elements in each iterable.

    >> flatten([[1,2], [3, [4, 5]]])
    [1,2,3,[4,5]]

    >> flatten([1, 2, 3])
    TypeError: 'int' object is not iterable
    """
  return [l for sublist in lis for l in sublist]


def coalesce(*args: Any) -> Any:
  """
    Returns the first non-None value, or None if no such value exists
    """
  return next((a for a in args if a is not None), None)


@deal.pre(lambda lis, predicate: all(isinstance(predicate(v), bool) for v in lis))
@deal.ensure(lambda lis, predicate, result: all(predicate(v) for v in result[0]))
@deal.ensure(lambda lis, predicate, result: not any(predicate(v) for v in result[1]))
@deal.raises(Exception, TypeError)
def partition(lis: Sequence[T], predicate: Callable[[T], bool]) -> tuple[list[T], list[T]]:
  """
    Splits a list into two lists based on a predicate. The first list will contain
    all elements of the provided list where predicate is true, and the second list
    will contain the rest
    """
  as_list = list(lis)
  true_list = []
  false_list = []
  for l in as_list:
    pred_value = predicate(l)
    if pred_value:
      true_list.append(l)
    else:
      false_list.append(l)

  return true_list, false_list


@deal.ensure(lambda lis, result: set(lis) == set(result))
@deal.post(lambda result: len(result) == len(set(result)))
@deal.pure
def distinct(lis: list[THashable] | tuple[THashable, ...]) -> Sequence[THashable]:
  """
    Returns a copy of lis with only distinct elements, preserving order.
    """
  return distinct_by(lis, key=identity)


@deal.ensure(lambda lis, key, result: set(key(v) for v in lis) == set(key(v) for v in result))
@deal.raises(Exception)
def distinct_by(lis: Sequence[T], key: Callable[[T], Hashable]) -> Sequence[T]:
  """
    Returns a copy of lis with only distinct elements, using the function `key` to determine distinctness.
    When two elements have the same key value, the first encountered is used
    """

  @unsafe_generator
  def generator() -> Iterator[T]:
    seen = set()
    for l in lis:
      k = key(l)
      if k not in seen:
        seen.add(k)
        yield l

  gen = generator()
  if isinstance(lis, list):
    return list(gen)
  if isinstance(lis, tuple):
    return tuple(gen)
  raise ValueError(f"Invalid type for compact: {type(lis)}")


def max_option(
  lis: Iterable[T],
  key: Callable[[T], "type_Comparable"] | Sentinel = Sentinel.NO_ARG,
) -> Optional[T]:
  """
    Like max, but returns None on an empty seq instead of an error
    """
  try:
    if key == Sentinel.NO_ARG:
      return max(lis)  # type: ignore
    assert not isinstance(key, Sentinel)
    return max(lis, key=key)
  except ValueError:
    return None


def min_option(
  lis: Iterable[T],
  key: Callable[[T], "type_Comparable"] | Sentinel = Sentinel.NO_ARG,
) -> Optional[T]:
  """
    Like min, but returns None on an empty seq instead of an error
    """
  try:
    if key == Sentinel.NO_ARG:
      return min(lis)  # type: ignore
    assert not isinstance(key, Sentinel)
    return min(lis, key=key)
  except ValueError:
    return None


@deal.ensure(lambda lis, index, result: result == lis[index] if -len(lis) <= index < len(lis) else result is None)
@deal.pure
def list_get(lis: Sequence[T], index: int) -> Optional[T]:
  """
    Gets the list item at the provided index, or None if that index is invalid
    """
  try:
    return lis[index]
  except IndexError:
    return None


@deal.pre(lambda lis, n: n >= 0)
@deal.ensure(lambda lis, n, result: len(lis) >= len(result))
@deal.ensure(lambda lis, n, result: len(result) == n if n < len(lis) else len(result) == len(lis))
@deal.ensure(lambda lis, n, result: lis[-len(result) :] == result if result else True)
@deal.pure
def tail(lis: Sequence[T], n: int) -> Sequence[T]:
  """
    Gets the last N items of a list.
    This is safer than lis[-n:], because it will still work when n is 0.
    It also fails on None inputs instead of just returning the whole list
    """
  return [] if n <= 0 else lis[-n:]


def chunked(
  lis: Iterable[T],
  size: int,
  fillvalue: Optional[T] = None,
) -> list[tuple[Optional[T], ...]]:
  """
    Returns disjoint list slices of length `size`, in order. Returns a list of tuples.
    Uses `fillvalue` to pad out the last list, if necessary.

    Ex: chunked([1,2,3,4], 2) == [(1, 2), (3, 4)]
    """
  if size < 1:
    raise Exception(f"Size must be > 0, received {size}")
  args = [iter(lis)] * size
  return list(itertools.zip_longest(fillvalue=fillvalue, *args))


@deal.pre(lambda lis, size: size > 0)
@deal.ensure(lambda lis, size, result: all(len(v) == size for v in result))
@deal.ensure(lambda lis, size, result: all(tuple(lis[i : i + size]) == v for i, v in enumerate(result)))
@deal.pure
def sliding(lis: Sequence[T], size: int) -> list[tuple[T, ...]]:
  """
    Returns all list slices of length `size`, in order. Returns a list of tuples.

    Ex: sliding([1,2,3,4], 2) == [(1, 2), (2, 3), (3, 4)]
    """
  list_iterators = itertools.tee(lis, size)
  for index, list_iterator in enumerate(list_iterators):
    next(itertools.islice(list_iterator, index, index), None)  # advance by `index`
  return list(zip(*list_iterators))


@deal.ensure(lambda val, result: (val,) == result if isinstance(val, bytes) else True)
@deal.ensure(lambda val, result: (val,) == result if isinstance(val, str) else True)
@deal.ensure(lambda val, result: (val,) == result if not isinstance(val, collections.abc.Iterable) else True)
@deal.ensure(lambda val, result: tuple(val) == result if isinstance(val, list) else True)
@deal.ensure(lambda val, result: tuple(val) == result if isinstance(val, tuple) else True)
@deal.post(lambda result: isinstance(result, tuple))
@deal.pure
def as_tuple(val: Collection[T] | T) -> tuple[T, ...]:
  """
    Turns a value into a tuple if it is not already iterable
    Allows creating functions that take either a single value
    or a list of values
    """
  if is_iterable(val):
    assert isinstance(val, collections.abc.Iterable)
    return tuple(val)
  return tuple([val])  # type: ignore
