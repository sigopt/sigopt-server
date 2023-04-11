# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Tests for the ``numbers`` module in ``sigopt-server``."""
import json
import math

import numpy
import pytest

from zigopt.common.numbers import *


LONG_NUMBER = 100000000000000000000000


class TestNumbers:
  def test_is_boolean(self):
    assert is_boolean(True) is True
    assert is_boolean(False) is True

    assert is_boolean(int("3")) is False
    assert is_boolean(0) is False
    assert is_boolean(LONG_NUMBER) is False
    assert is_boolean(numpy.int32(1)) is False
    assert is_boolean(numpy.int64(1)) is False
    assert is_boolean([]) is False
    assert is_boolean([2]) is False
    assert is_boolean({1: 2}) is False
    assert is_boolean(None) is False
    assert is_boolean(4.0) is False
    assert is_boolean("3") is False
    assert is_boolean(3.14) is False
    assert is_boolean(numpy.float32(1.0)) is False
    assert is_boolean(numpy.float64(1.0)) is False
    assert is_boolean(numpy.nan) is False
    assert is_boolean(numpy.inf) is False
    assert is_boolean(math.nan) is False
    assert is_boolean(math.inf) is False

  def test_is_integer(self):
    assert is_integer(int("3")) is True
    assert is_integer(0) is True
    assert is_integer(LONG_NUMBER) is True
    assert is_integer(numpy.int32(1)) is True
    assert is_integer(numpy.int64(1)) is True

    assert is_integer([]) is False
    assert is_integer([2]) is False
    assert is_integer({1: 2}) is False
    assert is_integer(None) is False
    assert is_integer(True) is False
    assert is_integer(False) is False
    assert is_integer(4.0) is False
    assert is_integer("3") is False
    assert is_integer(3.14) is False
    assert is_integer(numpy.float32(1.0)) is False
    assert is_integer(numpy.float64(1.0)) is False
    assert is_integer(numpy.nan) is False
    assert is_integer(numpy.inf) is False
    assert is_integer(math.nan) is False
    assert is_integer(math.inf) is False

  def test_is_integer_valued_number(self):
    assert is_integer_valued_number(int("3")) is True
    assert is_integer_valued_number(0) is True
    assert is_integer_valued_number(LONG_NUMBER) is True
    assert is_integer_valued_number(numpy.int32(1)) is True
    assert is_integer_valued_number(numpy.int64(1)) is True
    assert is_integer_valued_number(4.0) is True
    assert is_integer_valued_number(numpy.float32(0.0)) is True
    assert is_integer_valued_number(numpy.float64(0.0)) is True

    assert is_integer_valued_number([]) is False
    assert is_integer_valued_number([2]) is False
    assert is_integer_valued_number({1: 2}) is False
    assert is_integer_valued_number(None) is False
    assert is_integer_valued_number(True) is False
    assert is_integer_valued_number(False) is False
    assert is_integer_valued_number("3") is False
    assert is_integer_valued_number(3.14) is False
    assert is_integer_valued_number(numpy.float32(0.5)) is False
    assert is_integer_valued_number(numpy.float64(0.5)) is False
    assert is_integer_valued_number(numpy.nan) is False
    assert is_integer_valued_number(numpy.inf) is False
    assert is_integer_valued_number(math.nan) is False
    assert is_integer_valued_number(math.inf) is False

  def test_is_number(self):
    assert is_number(int("3")) is True
    assert is_number(0) is True
    assert is_number(LONG_NUMBER) is True
    assert is_number(4.0) is True
    assert is_number(3.14) is True
    assert is_number(numpy.int32(1)) is True
    assert is_number(numpy.int64(1)) is True
    assert is_number(numpy.float32(1.0)) is True
    assert is_number(numpy.float64(1.0)) is True

    assert is_number([]) is False
    assert is_number([2]) is False
    assert is_number({1: 2}) is False
    assert is_number(None) is False
    assert is_number(True) is False
    assert is_number(False) is False
    assert is_number("3") is False
    assert is_number(numpy.nan) is False
    assert is_number(numpy.inf) is False
    assert is_number(math.nan) is False
    assert is_number(math.inf) is False


class TestIsNaN:
  """
    Usually in unit tests we would check assert is_nan(test) is False or is True, but here we sometimes get
    False or numpy.bool_(False), which are harder to compare. We're using assert is_nan(test) and assert not
    is_nan(test) to mimic how we would do if is_nan(x): if not is_nan(x): in the zigopt code base.
    """

  @pytest.mark.parametrize("test", [float("nan"), numpy.nan, json.loads("NaN")])
  def test_nan(self, test):
    assert is_nan(test)

  @pytest.mark.parametrize("test", [-1000000, 0, 1000000, math.inf, -math.inf])
  def test_float(self, test):
    assert not is_nan(test)

  @pytest.mark.parametrize("test", [-LONG_NUMBER, LONG_NUMBER])
  def test_long(self, test):
    assert not is_nan(test)

  def test_float_array(self):
    with pytest.raises(TypeError):
      assert all(not x for x in is_nan([-1000000, 0, 1000000]))

  def test_long_array(self):
    with pytest.raises(TypeError):
      assert all(not x for x in is_nan([-LONG_NUMBER, LONG_NUMBER]))

  @pytest.mark.parametrize("test", [False, True, None])
  def test_misc_values(self, test):
    assert not is_nan(test)
