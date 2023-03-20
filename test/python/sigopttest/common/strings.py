# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math

import numpy

from zigopt.common.strings import *


class TestStrings(object):
  def test_is_string(self):
    assert is_string("") is True
    assert is_string("3") is True
    assert is_string("abc") is True
    assert is_string("abc") is True

    assert is_string(b"abc") is False
    assert is_string(int("3")) is False
    assert is_string(0) is False
    assert is_string(numpy.int32()) is False
    assert is_string(numpy.int64()) is False
    assert is_string([]) is False
    assert is_string([2]) is False
    assert is_string({1: 2}) is False
    assert is_string(None) is False
    assert is_string(True) is False
    assert is_string(False) is False
    assert is_string(4.0) is False
    assert is_string(3.14) is False
    assert is_string(numpy.float32()) is False
    assert is_string(numpy.float64()) is False
    assert is_string(numpy.nan) is False
    assert is_string(numpy.inf) is False
    assert is_string(math.nan) is False
    assert is_string(math.inf) is False

  def is_serial(self):
    assert is_serial("") is True
    assert is_serial("abc") is True
    assert is_serial("abc") is True
    assert is_serial(b"") is True
    assert is_serial(b"abc") is True
    assert is_serial("abc") is True

    assert is_serial(int("3")) is False
    assert is_serial(0) is False
    assert is_serial(numpy.int32()) is False
    assert is_serial(numpy.int64()) is False
    assert is_serial([]) is False
    assert is_serial([2]) is False
    assert is_serial({1: 2}) is False
    assert is_serial(None) is False
    assert is_serial(True) is False
    assert is_serial(False) is False
    assert is_serial(4.0) is False
    assert is_serial(3.14) is False
    assert is_serial(numpy.float32()) is False
    assert is_serial(numpy.float64()) is False
    assert is_serial(numpy.nan) is False
    assert is_serial(numpy.inf) is False
    assert is_serial(math.nan) is False
    assert is_serial(math.inf) is False
