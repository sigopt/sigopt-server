# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common import *
from zigopt.observation.model import *
from zigopt.optimize.args import *


class TestOptimizationArgs:
  def make_args(self, ids):
    return OptimizationArgs(
      source=None,
      observation_iterator=[Observation(id=i) for i in ids],
      observation_count=len(ids),
      failure_count=0,
      max_observation_id=max_option(ids),
      old_hyperparameters=None,
      open_suggestions=[],
      last_observation=None,
    )

  @pytest.fixture(params=([], [1, 2, 3]))
  def ids(self, request):
    return request.param

  def test_iterator(self, ids):
    assert [o.id for o in self.make_args(ids).observation_iterator] == ids

  def test_cant_consume_twice(self, ids):
    args = self.make_args(ids)
    iterator = args.observation_iterator
    list(iterator)
    with pytest.raises(ValueError):
      list(iterator)
