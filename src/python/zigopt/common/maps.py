# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# crosshair: on
import collections
from typing import Callable, Collection, Hashable, Mapping, MutableMapping, TypeVar

import deal


T = TypeVar("T")
R = TypeVar("R")
THashable = TypeVar("THashable", bound=Hashable)
GHashable = TypeVar("GHashable", bound=Hashable)


__all__ = [
  "map_dict",
  "filter_keys",
  "extend_dict",
  "invert_dict",
  "generate_constant_map_and_inverse",
  "omit",
  "pick",
  "as_grouped_dict",
  "to_map_by_key",
]


@deal.ensure(lambda func, d, result: all(func(v) == result[k] for k, v in d.items()))
def map_dict(func: Callable[[T], R], d: dict[GHashable, T]) -> dict[GHashable, R]:
  """
    Returns a new dict with `func` applied to all the values in `d`
    """
  return dict(((key, func(value)) for (key, value) in d.items()))


@deal.ensure(lambda func, json, result: set(result) == {k for k in json if func(k)})
@deal.ensure(lambda func, json, result: all(json[k] is v for k, v in result.items()))
@deal.raises(Exception)
def filter_keys(func: Callable[[GHashable], bool], json: dict[GHashable, T]) -> dict[GHashable, T]:
  return {key: value for key, value in json.items() if func(key)}


@deal.pre(lambda base, dicts: isinstance(base, collections.abc.MutableMapping))
@deal.pre(lambda base, dicts: all(isinstance(d, collections.abc.Mapping) for d in dicts))
def _extend_dict(
  base: MutableMapping[GHashable, T], dicts: tuple[Mapping[GHashable, T], ...]
) -> MutableMapping[GHashable, T]:
  for d in dicts:
    base.update(d)
  return base


def extend_dict(base: MutableMapping[GHashable, T], *dicts: Mapping[GHashable, T]) -> MutableMapping[GHashable, T]:
  """
    Extends dict `base` with entries from `dicts`.
    Matches underscore.js _.extend.
    Modifies 'a'. if you want to leave the arguments
    unmodified, pass an empty dict as the first argument (so that the
    only dict modified is an anonymous one).

    >> extend_dict(dict(a=1, b=2), dict(a=3, c=4)) == dict(a=3, b=2, c=4)
    True
    """
  return _extend_dict(base, dicts)


@deal.ensure(lambda base, result: all(base[v] is k for k, v in result.items()))
@deal.ensure(lambda base, result: all(result[v] is k for k, v in base.items()))
@deal.raises(ValueError)
@deal.reason(ValueError, lambda base: len(set(base.values())) != len(base))
def invert_dict(base: Mapping[GHashable, THashable]) -> dict[THashable, GHashable]:
  """
    Returns a new dict which has the keys and values of the input reversed
    """
  ret = {}
  for k, v in base.items():
    ret[v] = k
  if len(ret) != len(base):
    raise ValueError("Duplicate value found in provided dict, could not invert")
  return ret


def generate_constant_map_and_inverse(
  base: Mapping[GHashable, THashable]
) -> tuple[dict[GHashable, THashable], dict[THashable, GHashable]]:
  """
    A shorthand to generate bi-directional mappings for named constants.
    An example,

    NAME_TO_TYPE, TYPE_TO_NAME = generate_constant_map_and_inverse(dict(
      name1=type1,
      name2=type2,
    ))
    """
  return dict(base), invert_dict(base)


@deal.ensure(lambda base, keys, result: set(base) - set(keys) == set(result))
@deal.ensure(lambda base, keys, result: all(base[k] is result[k] for k in result))
def _omit(base: Mapping[GHashable, T], keys: tuple[GHashable, ...]) -> dict[GHashable, T]:
  keys_ = set(keys)
  return {k: v for k, v in base.items() if k not in keys_}


def omit(base: Mapping[GHashable, T], *keys: GHashable) -> dict[GHashable, T]:
  """
    Returns a copy of `base` with `keys` removed.
    Matches underscore.js _.omit.
    """
  return _omit(base, keys)


@deal.ensure(lambda base, keys, result: set(base) & set(keys) == set(result))
@deal.ensure(lambda base, keys, result: all(base[k] is result[k] for k in result))
@deal.pure
def _pick(
  base: Mapping[GHashable, T],
  keys: tuple[GHashable, ...],
) -> dict[GHashable, T]:
  keys_ = set(keys)
  return {k: v for k, v in base.items() if k in keys_}


def pick(base: Mapping[GHashable, T], *keys: GHashable) -> dict[GHashable, T]:
  """
    Returns a copy of `base` with only keys `keys`.
    Matches underscore.js _.pick.
    """
  return _pick(base, keys)


@deal.ensure(lambda lis, key, result: all(all(key(v) == k for v in group) for k, group in result.items()))
@deal.ensure(lambda lis, key, result: all(v in result[key(v)] for v in lis))
@deal.raises(Exception)
def as_grouped_dict(lis: Collection[T], key: Callable[[T], GHashable]) -> dict[GHashable, list[T]]:
  """
    Groups the elements in lis by applying the function `key`
    This is just like itertools.groupby, but does not require keys to be consecutive in order to be grouped.
    """
  ret_map: dict[GHashable, list[T]] = {}
  for l in lis:
    key_val = key(l)
    try:
      ret_map.setdefault(key_val, []).append(l)
    except TypeError as e:
      raise TypeError(f"Unhashable object of type {type(key_val)}: {key_val!r}") from e
  return ret_map


@deal.ensure(lambda lis, key, result: {key(v) for v in lis} == set(result))
@deal.ensure(lambda lis, key, result: all(any(v is e for e in lis) for v in result.values()))
@deal.raises(Exception)
def to_map_by_key(lis: Collection[T], key: Callable[[T], GHashable]) -> dict[GHashable, T]:
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
