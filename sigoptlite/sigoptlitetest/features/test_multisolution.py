# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestMultisolutionExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.mark.parametrize("bad_num_sol", [-1, 0])
  def test_multisolution_wrong_num_solutions(self, bad_num_sol):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["num_solutions"] = bad_num_sol
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = ".num_solutions must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_multisolution_too_many_num_solutions(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    experiment_meta["num_solutions"] = experiment_meta["observation_budget"] + 1
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "observation_budget needs to be larger than the number of solutions"
    assert exception_info.value.args[0] == msg

  def test_multisolution_multitask_incompatible(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta["num_solutions"] = 5
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment with multiple solutions cannot be multitask"
    assert exception_info.value.args[0] == msg

  def test_multisolution_no_budget_forbidden(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    experiment_meta.pop("observation_budget")
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with multiple solutions"
    assert exception_info.value.args[0] == msg
