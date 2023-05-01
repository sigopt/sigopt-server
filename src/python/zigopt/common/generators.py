# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import collections.abc as _collectionsabc
from typing import Callable, Generic, Iterable, ParamSpec, TypeVar


lists_T = TypeVar("lists_T")
lists_G = TypeVar("lists_G")
lists_P = ParamSpec("lists_P")
lists_TCallable = TypeVar("lists_TCallable", bound=Callable)

__all__ = ["generator_to_list", "generator_to_safe_iterator", "generator_to_dict", "safe_iterator", "unsafe_generator"]


def generator_to_list(func: Callable[lists_P, Iterable[lists_T]]) -> Callable[lists_P, list[lists_T]]:
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
  func: Callable[lists_P, Iterable[lists_T]]
) -> Callable[lists_P, "safe_iterator[lists_T]"]:
  def make_safe_iterator(*args, **kwargs):
    return safe_iterator(func(*args, **kwargs))

  return make_safe_iterator


def generator_to_dict(
  func: Callable[lists_P, Iterable[tuple[lists_G, lists_T]]]
) -> Callable[lists_P, dict[lists_G, lists_T]]:
  def make_dict(*args, **kwargs):
    return dict(func(*args, **kwargs))

  return make_dict


class safe_iterator(Generic[lists_T]):
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


def unsafe_generator(func: lists_TCallable) -> lists_TCallable:
  """
    A marker to indicate that we are acknowledging that this generator
    can't be used repeatedly. Useful for interfacing with external libraries
    that expect instances of types.GeneratorType
    """
  return func
