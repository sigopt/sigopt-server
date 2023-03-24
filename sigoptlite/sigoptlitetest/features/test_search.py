# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestSearchExperiment(UnitTestsBase):
  @pytest.fixture
  def conn(self):
    return Connection(driver=LocalDriver)

  def test_search_no_budget_forbidden(self, conn):
    experiment_meta = self.get_experiment_feature("search")
    experiment_meta.pop("observation_budget")
    with pytest.raises(ValueError) as exception_info:
      conn.experiments().create(**experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with constraint metrics"
    assert exception_info.value.args[0] == msg

  def test_search_multisolution_incompatible(self, conn):
    experiment_meta = self.get_experiment_feature("search")
    experiment_meta["num_solutions"] = 5
    with pytest.raises(ValueError) as exception_info:
      conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment with multiple solutions require exactly one optimized metric"
    assert exception_info.value.args[0] == msg
