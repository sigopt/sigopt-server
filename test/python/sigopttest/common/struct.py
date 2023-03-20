# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from zigopt.common.struct import ImmutableStruct


# pylint: disable=comparison-with-itself
# pylint: disable=pointless-statement
# pylint: disable=unsubscriptable-object
# pylint: disable=not-an-iterable

point_cls_without_defaults = ImmutableStruct("Point", ["x", "y"])
point_cls_with_defaults = ImmutableStruct("Point", ["x", "y"], defaults=[5, 6])


@pytest.fixture(params=[point_cls_with_defaults, point_cls_without_defaults])
def point_cls(request):
  return request.param


def test_struct(point_cls):
  point = point_cls(1, 2)
  assert point.x == 1
  assert point.y == 2
  assert point.__class__.__name__ == "Point"


def test_eq(point_cls):
  point = point_cls(1, 2)
  assert point == point_cls(1, 2)
  assert point_cls(1, 2) == point_cls(1, 2)
  assert point != point_cls(3, 4)

  assert hash(point) == hash(point)
  assert hash(point) == hash(point_cls(1, 2))


def test_copy(point_cls):
  point = point_cls(1, 2)
  assert point == point
  assert id(point) == id(point)

  copied = copy.copy(point)
  assert point == copied
  assert id(point) != id(copied)

  deep_copied = copy.deepcopy(point)
  assert point == deep_copied
  assert id(point) != id(deep_copied)


def test_repr(point_cls):
  point = point_cls(1, 2)
  assert repr(point) == "Point(x=1, y=2)"


def test_nested(point_cls):
  point = point_cls(point_cls(1, 2), point_cls(3, 4))
  assert point.x.x == 1
  assert point.x.y == 2
  assert point.y.x == 3
  assert point.y.y == 4


def test_not_tuple(point_cls):
  point = point_cls(1, 2)

  with pytest.raises(TypeError):
    len(point)

  with pytest.raises(TypeError):
    for _ in point:
      pass

  with pytest.raises(TypeError):
    point[0]

  with pytest.raises(TypeError):
    point[0:1]


def test_defaults():
  point = point_cls_with_defaults()
  assert point.x == 5
  assert point.y == 6
  assert point.__class__.__name__ == "Point"


def test_error_with_no_defaults():
  with pytest.raises(TypeError):
    point_cls_without_defaults()


def test_incomplete_defaults():
  with pytest.raises(AssertionError):
    ImmutableStruct("Point", ["x", "y"], defaults=[1])

  with pytest.raises(AssertionError):
    ImmutableStruct("Point", ["x", "y"], defaults=[])
