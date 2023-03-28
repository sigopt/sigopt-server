# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestLocalDriver(UnitTestsBase):
  def test_best_assignments(self):
    num_obs = 10
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    for i in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )

    best_assignments = conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 1
    assert len(best_assignments.data) == 1
    assert best_assignments.data[0].values[0].value == num_obs - 1

    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["type"] = "random"

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    for _ in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": numpy.random.rand()}, {"name": "y2", "value": numpy.random.rand()}],
      )

    best_assignments = conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count >= 1
    assert len(best_assignments.data) >= 1
