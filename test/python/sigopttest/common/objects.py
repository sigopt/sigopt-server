# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import MagicMock, Mock

from zigopt.common import *


class TestObjects(object):
  @pytest.mark.parametrize(
    "obj,instances,result",
    [
      ({"key": 6}, Mock, False),
      ({"key": 6}, int, True),
      ({"key": Mock()}, Mock, True),
      ({"key": {"deep_key": MagicMock()}}, (Mock, MagicMock), True),
      ({"key": {"deep_key": "deep_value"}}, (Mock, MagicMock), False),
    ],
  )
  def test_recursively_check_for_instances_simple(self, obj, instances, result):
    assert recursively_check_for_instances(obj, instances) == result

  def test_recursively_check_for_instances_loops(self):
    obj1 = {"key": {"deep_key": 1, "deep_object": {"deeper_key": Mock()}, "loop_key": None}}
    obj2 = {"key": {"deep_key": "1", "loop_key": obj1}}
    obj1["key"]["loop_key"] = obj2
    assert recursively_check_for_instances(obj1, int) is True
    assert recursively_check_for_instances(obj2, int) is True
    assert recursively_check_for_instances(obj1, Mock) is True
    assert recursively_check_for_instances(obj2, Mock) is True
    assert recursively_check_for_instances(obj1, float) is False
    assert recursively_check_for_instances(obj2, float) is False
