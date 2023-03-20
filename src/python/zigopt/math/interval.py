# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from abc import ABCMeta, abstractmethod
from collections import namedtuple


class Interval(namedtuple("BaseInterval", ("min", "max")), metaclass=ABCMeta):
  __slots__ = ()

  def __repr__(self):
    return f"{self.__class__.__name__}({self.min},{self.max})"

  @abstractmethod
  def __contains__(self, key):
    pass

  def closure(self):
    return ClosedInterval(self.min, self.max)

  def interior(self):
    return OpenInterval(self.min, self.max)

  # overridden for ClosedInterval
  def __nonzero__(self):
    return self.min < self.max

  def __bool__(self):
    return self.__nonzero__()

  def __eq__(self, other):
    return self.__class__ == other.__class__ and self.min == other.min and self.max == other.max

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash((self.min, self.max))

  @property
  def length(self):
    return self.max - self.min

  def is_inside(self, value):
    return value in self

  def is_valid(self):
    return self.max >= self.min


class OpenInterval(Interval):
  def __contains__(self, key):
    return self.min < key < self.max


class ClosedInterval(Interval):
  def __contains__(self, key):
    return self.min <= key <= self.max

  def __nonzero__(self):
    return self.min <= self.max

  def __bool__(self):
    return self.__nonzero__()


class LeftOpenInterval(Interval):
  def __contains__(self, key):
    return self.min < key <= self.max


class RightOpenInterval(Interval):
  def __contains__(self, key):
    return self.min <= key < self.max
