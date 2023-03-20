# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common import *


class TestFunctions(object):
  @pytest.mark.parametrize("value", [1, None, (2, 3, 4), "hello"])
  def test_identity(self, value):
    assert identity(value) is value

  @pytest.mark.parametrize("value", [1, (1, 3, 2), "hello"])
  def test_napply_applies(self, value):
    returned = []

    def should_run(obj):
      assert obj is value
      return returned

    assert napply(value, should_run) is returned

  def test_napply_skips(self):
    def shouldnt_run(obj):
      raise Exception()

    assert napply(None, shouldnt_run) is None

  @pytest.mark.parametrize(
    "exc,func,args",
    [
      (AttributeError, getattr, ([], "not_a_list_attr")),
      (IndexError, lambda x: x[0], ([],)),
      (ValueError, int, ("not an int",)),
    ],
  )
  def test_does_throw(self, exc, func, args):
    assert throws(exc, func, *args)

  @pytest.mark.parametrize(
    "exc,func,args",
    [
      (AttributeError, getattr, ([], "__len__")),
      (IndexError, lambda x: x[0], ([1],)),
      (ValueError, int, ("42",)),
    ],
  )
  def test_does_not_throw(self, exc, func, args):
    assert not throws(exc, func, *args)

  @pytest.mark.parametrize(
    "exc,func,args",
    [
      (AttributeError, getattr, ([], "not_a_list_attr")),
      (IndexError, lambda x: x[0], ([],)),
      (ValueError, int, ("not an int",)),
    ],
  )
  def test_throws_does_not_catch(self, exc, func, args):
    pytest.raises(exc, throws, MemoryError, func, *args)
