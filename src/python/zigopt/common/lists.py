# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""
Common utility functions for working with lists
"""

import collections.abc as _collectionsabc
import enum
import itertools as _itertools
from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import Any as _Any
from typing import Callable as _Callable
from typing import Generic as _Generic
from typing import Hashable as _Hashable
from typing import Iterable as _Iterable
from typing import Iterator as _Iterator
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import ParamSpec as _ParamSpec
from typing import Sequence as _Sequence
from typing import Set as _Set
from typing import TypeVar as _TypeVar

import numpy as _numpy

from zigopt.common.functions import identity as _identity
from zigopt.common.strings import is_serial as _is_serial


if _TYPE_CHECKING:
  import _typeshed

  type_lists_Comp = _typeshed.SupportsRichComparison


lists_T = _TypeVar("lists_T")
lists_G = _TypeVar("lists_G")
lists_R = _TypeVar("lists_R")
lists_P = _ParamSpec("lists_P")
lists_TCallable = _TypeVar("lists_TCallable", bound=_Callable)
lists_THashable = _TypeVar("lists_THashable", bound=_Hashable)
lists_GHashable = _TypeVar("lists_GHashable", bound=_Hashable)


class Sentinel(enum.Enum):
  NO_ARG = 0


def generator_to_list(func: _Callable[lists_P, _Iterable[lists_T]]) -> _Callable[lists_P, list[lists_T]]:
  """
    Decorator that turns a generator function into one that returns a list.
    In general, functions that return lists are preferable to those that return
    generators, because lists have fewer surprises (they can be iterated over multiple
    times, can be indexed, etc.). But sometimes writing the function as a generator
    is cleaner. This decorator makes working in such situations nicer.

    This decorator consumes the whole generator function.

    @generator_to_list
    def walk_tree(tree):
      yield tree.item
      for t in walk_tree(tree.left):
        yield t
      for t in walk_tree(tree.right):
        yield t

    walk_tree(t)  # Returns a list
    """

  def make_list(*args, **kwargs):
    ret = []
    for v in func(*args, **kwargs):
      ret.append(v)
    return ret

  return make_list


def generator_to_safe_iterator(
  func: _Callable[lists_P, _Iterable[lists_T]]
) -> _Callable[lists_P, "safe_iterator[lists_T]"]:
  def make_safe_iterator(*args, **kwargs):
    return safe_iterator(func(*args, **kwargs))

  return make_safe_iterator


def generator_to_dict(
  func: _Callable[lists_P, _Iterable[tuple[lists_G, lists_T]]]
) -> _Callable[lists_P, dict[lists_G, lists_T]]:
  def make_dict(*args, **kwargs):
    return dict(func(*args, **kwargs))

  return make_dict


def flatten(lis: _Iterable[_Iterable[lists_T]]) -> list[lists_T]:
  """
    :param lis: A list of iterables
    Returns a list comprised of the elements in each iterable.

    >> flatten([[1,2], [3, [4, 5]]])
    [1,2,3,[4,5]]

    >> flatten([1, 2, 3])
    TypeError: 'int' object is not iterable
    """
  return [l for sublist in lis for l in sublist]


def compact_map(dct: _Mapping[lists_GHashable, _Optional[lists_T]]) -> dict[lists_GHashable, lists_T]:
  return {k: v for k, v in dct.items() if v}


def compact_sequence(lis: _Sequence[_Optional[lists_T]], cls: type[list] | type[tuple]) -> _Sequence[lists_T]:
  return cls(l for l in lis if l)


def compact(
  lis: _Mapping[lists_GHashable, _Optional[lists_T]] | _Sequence[_Optional[lists_T]]
) -> dict[lists_GHashable, lists_T] | _Sequence[lists_T]:
  """
    Returns a copy of this object with all falsy values removed.
    """
  if is_mapping(lis):
    assert isinstance(lis, _collectionsabc.Mapping)
    return compact_map(lis)
  if isinstance(lis, list | tuple):
    return compact_sequence(lis, type(lis))
  raise ValueError(f"Invalid type for compact: {type(lis)}")


def remove_nones_mapping(dct: _Mapping[lists_GHashable, _Optional[lists_T]]) -> dict[lists_GHashable, lists_T]:
  return {k: v for k, v in dct.items() if v is not None}


def remove_nones_set(lis: _Set[_Optional[lists_T]]) -> _Set[lists_T]:
  return {v for v in lis if v is not None}


def remove_nones_sequence(
  lis: _Sequence[_Optional[lists_T]], cls: type[list] | type[tuple]
) -> list[lists_T] | tuple[lists_T, ...]:
  return cls(l for l in lis if l is not None)


def remove_nones(
  lis: _Sequence[_Optional[lists_T]] | _Mapping[lists_GHashable, _Optional[lists_T]] | _Set[_Optional[lists_T]]
) -> _Sequence[lists_T] | _Mapping[lists_GHashable, lists_T] | _Set[lists_T]:
  """
    Returns a copy of this object with all `None` values removed.
    """
  if is_mapping(lis):
    assert isinstance(lis, _collectionsabc.Mapping)
    return remove_nones_mapping(lis)
  if is_set(lis):
    assert isinstance(lis, _collectionsabc.Set)
    return remove_nones_set(lis)
  if isinstance(lis, list | tuple):
    return remove_nones_sequence(lis, type(lis))
  raise ValueError(f"Invalid type for remove_nones: {type(lis)}")


def coalesce(*args: _Any) -> _Any:
  """
    Returns the first non-None value, or None if no such value exists
    """
  return list_get(remove_nones_sequence(args, tuple), 0)


def map_dict(func: _Callable[[lists_T], lists_R], d: dict[lists_GHashable, lists_T]) -> dict[lists_GHashable, lists_R]:
  """
    Returns a new dict with `func` applied to all the values in `d`
    """
  return dict(((key, func(value)) for (key, value) in d.items()))


def recursively_map_dict(func: _Callable[[_Any], _Any], d: dict) -> dict:
  def _inner(func, d):
    if is_mapping(d):
      return map_dict(lambda v: _inner(func, v), d)
    if is_sequence(d):
      return [_inner(func, v) for v in d]
    return func(d)

  assert is_mapping(d)
  return _inner(func, d)


def filter_keys(
  func: _Callable[[lists_GHashable], bool], json: dict[lists_GHashable, lists_T]
) -> dict[lists_GHashable, lists_T]:
  return {key: value for key, value in json.items() if func(key)}


def recursively_filter_keys(func: _Callable[[_Any], bool], json: _Any) -> _Any:
  def r_call(item):
    return recursively_filter_keys(func, item)

  if is_sequence(json):
    return [r_call(e) for e in json]

  if is_mapping(json):
    return map_dict(r_call, filter_keys(func, json))

  return json


def recursively_omit_keys(json: _Any, keys: _Sequence) -> _Any:
  assert is_sequence(keys)
  return recursively_filter_keys(lambda key: key not in keys, json)


def distinct_counts(lis: _Iterable[lists_GHashable]) -> dict[lists_GHashable, int]:
  """
    Returns the number of times each element occurs in `lis`.
    """
  ret: dict[lists_GHashable, int] = {}
  for l in lis:
    ret[l] = (ret.get(l) or 0) + 1
  return ret


def partition(lis: _Iterable[lists_T], predicate: _Callable[[lists_T], bool]) -> tuple[list[lists_T], list[lists_T]]:
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
    if pred_value is True:
      true_list.append(l)
    elif pred_value is False:
      false_list.append(l)
    else:
      raise Exception("Invalid predicate")

  return true_list, false_list


def distinct(lis: list[lists_T] | tuple[lists_T, ...]) -> _Sequence[lists_T]:
  """
    Returns a copy of lis with only distinct elements, preserving order.
    """
  return distinct_by(lis, key=_identity)


def distinct_by(lis: _Sequence[lists_T], key: _Callable[[lists_T], _Hashable]) -> _Sequence[lists_T]:
  """
    Returns a copy of lis with only distinct elements, using the function `key` to determine distinctness.
    When two elements have the same key value, the first encountered is used
    """

  @unsafe_generator
  def generator() -> _Iterator[lists_T]:
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


def find(lis: _Iterable[lists_T], predicate: _Callable[[lists_T], bool]) -> _Optional[lists_T]:
  """
    Finds the first element in lis satisfying predicate, or else None
    """
  return next((item for item in lis if predicate(item)), None)


def find_index(lis: _Iterable[lists_T], predicate: _Callable[[lists_T], bool]) -> _Optional[int]:
  """
    Finds the index of the first element in lis satisfying predicate, or else None
    """
  for index, item in enumerate(lis):
    if predicate(item):
      return index
  return None


def as_grouped_dict(
  lis: _Iterable[lists_T], key: _Callable[[lists_T], lists_GHashable]
) -> dict[lists_GHashable, list[lists_T]]:
  """
    Groups the elements in lis by applying the function `key`
    This is just like itertools.groupby, but does not require keys to be consecutive in order to be grouped.
    """
  ret_map: dict[lists_GHashable, list[lists_T]] = {}
  for l in lis:
    key_val = key(l)
    try:
      ret_map.setdefault(key_val, []).append(l)
    except TypeError as e:
      raise TypeError(f"Unhashable object of type {type(key_val)}: {key_val!r}") from e
  return ret_map


def to_map_by_key(
  lis: _Iterable[lists_T], key: _Callable[[lists_T], lists_GHashable]
) -> dict[lists_GHashable, lists_T]:
  """
    Creates a map out of the elements in lis by applying the function `key`.
    Assumes unique keys - if there are duplicate keys then a value will be chosen arbitrarily.
    """
  r = {}
  for l in lis:
    key_val = key(l)
    try:
      r[key_val] = l
    except TypeError as e:
      raise TypeError(f"Unhashable object of type {type(key_val)}: {key_val!r}") from e
  return r


def max_option(
  lis: _Iterable[lists_T], key: _Callable[[lists_T], "type_lists_Comp"] | Sentinel = Sentinel.NO_ARG
) -> _Optional[lists_T]:
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
  lis: _Iterable[lists_T], key: _Callable[[lists_T], "type_lists_Comp"] | Sentinel = Sentinel.NO_ARG
) -> _Optional[lists_T]:
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


def list_get(lis: _Sequence[lists_T], index: int) -> _Optional[lists_T]:
  """
    Gets the list item at the provided index, or None if that index is invalid
    """
  try:
    return lis[index]
  except IndexError:
    return None


def tail(lis: _Sequence[lists_T], n) -> _Sequence[lists_T]:
  """
    Gets the last N items of a list.
    This is safer than lis[-n:], because it will still work when n is 0.
    It also fails on None inputs instead of just returning the whole list
    """
  assert n is not None
  return [] if n <= 0 else lis[-n:]


def chunked(
  lis: _Iterable[lists_T], size: int, fillvalue: _Optional[lists_T] = None
) -> list[tuple[_Optional[lists_T], ...]]:
  """
    Returns disjoint list slices of length `size`, in order. Returns a list of tuples.
    Uses `fillvalue` to pad out the last list, if necessary.

    Ex: chunked([1,2,3,4], 2) == [(1, 2), (3, 4)]
    """
  if size < 1:
    raise Exception(f"Size must be > 0, received {size}")
  args = [iter(lis)] * size
  return list(_itertools.zip_longest(fillvalue=fillvalue, *args))


def sliding(lis: _Iterable[lists_T], size: int) -> list[tuple[lists_T, ...]]:
  """
    Returns all list slices of length `size`, in order. Returns a list of tuples.

    Ex: sliding([1,2,3,4], 2) == [(1, 2), (2, 3), (3, 4)]
    """
  if size < 1:
    raise Exception(f"Size must be > 0, received {size}")
  list_iterators = _itertools.tee(lis, size)
  for index, list_iterator in enumerate(list_iterators):
    next(_itertools.islice(list_iterator, index, index), None)  # advance by `index`
  return list(zip(*list_iterators))


def unsafe_generator(func: lists_TCallable) -> lists_TCallable:
  """
    A marker to indicate that we are acknowledging that this generator
    can't be used repeatedly. Useful for interfacing with external libraries
    that expect instances of types.GeneratorType
    """
  return func


def as_tuple(val: _Iterable[lists_T] | lists_T) -> tuple[lists_T, ...]:
  """
    Turns a value into a tuple if it is not already iterable
    Allows creating functions that take either a single value
    or a list of values
    """
  if is_iterable(val):
    assert isinstance(val, _collectionsabc.Iterable)
    return tuple(val)
  return tuple([val])  # type: ignore


def extend_dict(
  base: dict[lists_GHashable, lists_T], *dicts: _Mapping[lists_GHashable, lists_T]
) -> dict[lists_GHashable, lists_T]:
  """
    Extends dict `base` with entries from `dicts`.
    Matches underscore.js _.extend.
    Modifies 'a'. if you want to leave the arguments
    unmodified, pass an empty dict as the first argument (so that the
    only dict modified is an anonymous one).

    >> extend_dict(dict(a=1, b=2), dict(a=3, c=4)) == dict(a=3, b=2, c=4)
    True
    """
  assert is_mapping(base)
  for d in dicts:
    assert is_mapping(d)
    base.update(d)
  return base


def invert_dict(base: _Mapping[lists_GHashable, lists_THashable]) -> dict[lists_THashable, lists_GHashable]:
  """
    Returns a new dict which
    """
  assert is_mapping(base)
  ret = {}
  for k, v in base.items():
    ret[v] = k
  if len(ret) != len(base):
    raise ValueError("Duplicate value found in provided dict, could not invert")
  return ret


def generate_constant_map_and_inverse(
  base: _Mapping[lists_GHashable, lists_THashable]
) -> tuple[dict[lists_GHashable, lists_THashable], dict[lists_THashable, lists_GHashable]]:
  """
    A shorthand to generate bi-directional mappings for named constants.
    An example,

    NAME_TO_TYPE, TYPE_TO_NAME = generate_constant_map_and_inverse(dict(
      name1=type1,
      name2=type2,
    ))
    """
  return dict(base), invert_dict(base)


def omit(base: _Mapping[lists_GHashable, lists_T], *keys: lists_GHashable) -> dict[lists_GHashable, lists_T]:
  """
    Returns a copy of `base` with `keys` removed.
    Matches underscore.js _.omit.
    """
  assert is_mapping(base)
  keys_ = set(keys)
  return {k: v for k, v in base.items() if k not in keys_}


def pick(base: _Mapping[lists_GHashable, lists_T], *keys: lists_GHashable) -> dict[lists_GHashable, lists_T]:
  """
    Returns a copy of `base` with only keys `keys`.
    Matches underscore.js _.pick.
    """
  assert is_mapping(base)
  keys_ = set(keys)
  return {k: v for k, v in base.items() if k in keys_}


def is_iterable(val: _Any) -> bool:
  """
    Returns True iff this is an iterable type. Avoids the common error that strings
    and bytes are iterable.
    """
  return isinstance(val, _collectionsabc.Iterable) and not _is_serial(val)


def is_sequence(val: _Any) -> bool:
  """
    Returns True iff this is a "list-like" type. Avoids the common error that strings
    and bytes are iterable, and handles numpy and protobufs correctly
    """
  return (isinstance(val, _collectionsabc.Sequence) and not _is_serial(val)) or isinstance(val, _numpy.ndarray)


def is_mapping(val: _Any) -> bool:
  """
    Returns True iff this is a "dict-like" type
    """
  return isinstance(val, _collectionsabc.Mapping)


def is_set(val: _Any) -> bool:
  """
    Returns True iff this is a "set-like" type
    """
  return isinstance(val, _collectionsabc.Set)


class safe_iterator(_Generic[lists_T]):
  """
    Returns a new iterator that consumes from `iterator` but can only be
    consumed once. It will throw a ValueError if you try to consume from
    it after it has already been consumed
    """

  def __init__(self, underlying: _collectionsabc.Iterable[lists_T]):
    self._underlying = iter(underlying)
    self._exhausted = False

  def __iter__(self) -> _collectionsabc.Iterator[lists_T]:
    # pylint: disable=non-iterator-returned
    return self
    # pylint: enable=non-iterator-returned

  def __next__(self) -> lists_T:
    if self._exhausted:
      raise ValueError("Attempted to read from an exhausted iterator!")
    try:
      return next(self._underlying)
    except StopIteration:
      self._exhausted = True
      raise
