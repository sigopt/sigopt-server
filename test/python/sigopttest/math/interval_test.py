# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.math.interval import *


class TestInterval(object):
  def test_open(self):
    assert 2 in OpenInterval(1, 3)
    assert 4 not in OpenInterval(1, 3)
    assert 1 not in OpenInterval(1, 3)
    assert 3 not in OpenInterval(1, 3)

    assert 2 not in OpenInterval(1, 1)
    assert 1 not in OpenInterval(1, 1)
    assert 0 not in OpenInterval(1, 1)

    assert 3 not in OpenInterval(2, 1)
    assert 2 not in OpenInterval(2, 1)
    assert 1 not in OpenInterval(2, 1)
    assert 0 not in OpenInterval(2, 1)

  def test_closed(self):
    assert 2 in ClosedInterval(1, 3)
    assert 4 not in ClosedInterval(1, 3)
    assert 1 in ClosedInterval(1, 3)
    assert 3 in ClosedInterval(1, 3)

    assert 2 not in ClosedInterval(1, 1)
    assert 1 in ClosedInterval(1, 1)
    assert 0 not in ClosedInterval(1, 1)

    assert 3 not in ClosedInterval(2, 1)
    assert 2 not in ClosedInterval(2, 1)
    assert 1 not in ClosedInterval(2, 1)
    assert 0 not in ClosedInterval(2, 1)

    assert 2 in ClosedInterval(2, numpy.inf)
    assert numpy.inf in ClosedInterval(2, numpy.inf)
    assert 1 not in ClosedInterval(2, numpy.inf)

  def test_length(self):
    assert ClosedInterval(9.378, 9.378).length == 0
    assert ClosedInterval(-2.71, 3.14).length == 3.14 + 2.71
    assert ClosedInterval(-2.71, -3.14).length == -3.14 + 2.71
    assert ClosedInterval(0.0, numpy.inf).length == numpy.inf

  def test_is_empty(self):
    assert ClosedInterval(9.378, 9.378).is_valid()
    assert ClosedInterval(-2.71, 3.14).is_valid()
    assert not ClosedInterval(-2.71, -3.14).is_valid()
    assert ClosedInterval(0.0, numpy.inf).is_valid()
    assert not ClosedInterval(numpy.nan, 1.0).is_valid()

  def test_half_open(self):
    assert 2 in LeftOpenInterval(1, 3)
    assert 4 not in LeftOpenInterval(1, 3)
    assert 1 not in LeftOpenInterval(1, 3)
    assert 3 in LeftOpenInterval(1, 3)

    assert 2 not in LeftOpenInterval(1, 1)
    assert 1 not in LeftOpenInterval(1, 1)
    assert 0 not in LeftOpenInterval(1, 1)

    assert 3 not in LeftOpenInterval(2, 1)
    assert 2 not in LeftOpenInterval(2, 1)
    assert 1 not in LeftOpenInterval(2, 1)
    assert 0 not in LeftOpenInterval(2, 1)

    assert 2 in RightOpenInterval(1, 3)
    assert 4 not in RightOpenInterval(1, 3)
    assert 1 in RightOpenInterval(1, 3)
    assert 3 not in RightOpenInterval(1, 3)

    assert 2 not in RightOpenInterval(1, 1)
    assert 1 not in RightOpenInterval(1, 1)
    assert 0 not in RightOpenInterval(1, 1)

    assert 3 not in RightOpenInterval(2, 1)
    assert 2 not in RightOpenInterval(2, 1)
    assert 1 not in RightOpenInterval(2, 1)
    assert 0 not in RightOpenInterval(2, 1)
