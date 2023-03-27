# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection
from sigopt.exception import SigOptException

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

  @pytest.mark.parametrize(
    "tasks",
    [
      [0.1, 1],
      [dict(name="cheap"), dict(name="expensive")],
      [dict(name="cheap", cost=-0.1), dict(name="expensive", cost=1)],
      [dict(name="cheap", cost=1), dict(name="expensive", cost=2)],
      [dict(name="cheap", cost=0.1), dict(name="cheap", cost=1)],
      [dict(name="cheap", cost=0.1), dict(name="expensive", cost=0.1)],
      [dict(name="cheap", cost=0.1), dict(name="expensive", cost=0.9)],
    ],
  )
  def test_improper_tasks(self, conn, base_meta, tasks):
    experiment_meta = base_meta
    experiment_meta["tasks"] = tasks

    with pytest.raises(SigOptException):
      conn.experiments().create(**experiment_meta)

  def test_improper_task_costs(self, conn, base_meta):
    experiment_meta = base_meta
    experiment_meta["tasks"] = [dict(name="cheap", cost=-0.1), dict(name="expensive", cost=1)]

    with pytest.raises(SigOptException) as exception_info:
      conn.experiments().create(**experiment_meta)
    msg = ".cost must be greather than 0"
    assert exception_info.value.args[0] == msg

  def test_single_task_forbidden(self, conn, base_meta):
    experiment_meta = base_meta
    experiment_meta["tasks"] = [dict(name="cheap", cost=1)]
    with pytest.raises(SigOptException) as exception_info:
      conn.experiments().create(**experiment_meta)
    msg = "For multitask sigoptlite experiment, at least 2 tasks must be present"
    assert exception_info.value.args[0] == msg

  def test_multitask_no_observation_budget_forbidden(self, conn):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta.pop("observation_budget")
    with pytest.raises(SigOptException) as exception_info:
      conn.experiments().create(**experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with tasks (multitask)"
    assert exception_info.value.args[0] == msg
