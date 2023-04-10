# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from unittest.mock import Mock

import pytest

from zigopt.common import *
from zigopt.common.context import MultiContext


class ContextTestClass:
  def __init__(self, enter=None, exit_=None):
    self.enter = enter or Mock()
    self.exit = exit_ or Mock()

  def __enter__(self, *args, **kwargs):
    self.enter(*args, **kwargs)
    return self

  def __exit__(self, exc_type, *args, **kwargs):
    self.exit(*args, **kwargs)
    return False


class ContextTestException(Exception):
  pass


def test_multi_context_calls_exit_with_generator():
  c1 = ContextTestClass()

  @generator_to_safe_iterator
  def gen():
    yield c1
    raise ContextTestException()

  with pytest.raises(ContextTestException):
    with MultiContext(gen()) as (_, _):
      raise Exception("Should not enter block")


def test_multi_context():
  c1 = ContextTestClass()
  c2 = ContextTestClass()
  with pytest.raises(ContextTestException):
    with MultiContext(c for c in (c1, c2)) as (r1, r2):
      assert r1 is c1
      assert r2 is c2
      c1.enter.assert_called_with()
      c2.enter.assert_called_with()
      assert len(c2.exit.call_args_list) == 0
      assert len(c1.exit.call_args_list) == 0
      raise ContextTestException()
  assert len(c2.exit.call_args_list) == 1
  assert len(c1.exit.call_args_list) == 1
