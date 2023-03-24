# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase

class TestMultitask(UnitTestsBase):
  @pytest.fixture
  def conn(self):
    return Connection(driver=LocalDriver)

  @pytest.fixture
  def base_meta(self):
    return dict(
      parameters=[
        dict(name="x0", type="double", bounds=dict(min=0, max=1)),
        dict(name="x1", type="double", bounds=dict(min=0, max=1)),
        dict(name="x2", type="int", bounds=dict(min=0, max=100)),
        dict(name="x3", type="int", bounds=dict(min=0, max=100)),
        dict(name="x4", type="categorical", categorical_values=["c1", "c2"]),
      ],
      metrics=[dict(name="metric")],
      observation_budget=10,
    )

  @pytest.mark.parametrize("tasks", [
    [0.1, 1],
    [dict(name="cheap"), dict(name="expensive")],
    [dict(name="cheap", cost=1)],
    [dict(name="cheap", cost=-0.1), dict(name="expensive", cost=1)],
    [dict(name="cheap", cost=1), dict(name="expensive", cost=2)],
  ])
  def test_improper_tasks(self, conn, base_meta, tasks):
    experiment_meta = base_meta
    experiment_meta["tasks"] = tasks

    with pytest.raises(ValueError):
      conn.experiments().create(**experiment_meta)
