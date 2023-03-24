# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestSingleMetricExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("default")

  def test_missing_strategy_defaults_to_optimization(self, experiment_meta):
    del experiment_meta["metrics"][0]["strategy"]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].strategy == "optimize"

  def test_missing_objective_defaults_to_maximization(self, experiment_meta):
    del experiment_meta["metrics"][0]["objective"]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].objective == "maximize"

  def test_missing_objective_and_strategy_defaults_to_maximization_and_optimization(self, experiment_meta):
    del experiment_meta["metrics"][0]["strategy"]
    del experiment_meta["metrics"][0]["objective"]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].strategy == "optimize"
    assert e.metrics[0].objective == "maximize"

  @pytest.mark.parametrize("feature", ["multimetric", "metric_threshold", "metric_constraint", "search"])
  def test_incorrect_strategy_name(self, feature):
    strategy_name = "store"
    experiment_meta = self.get_experiment_feature(feature)
    experiment_meta["metrics"][0]["strategy"] = strategy_name
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = f"{strategy_name} is not one of the allowed values: optimize, constraint"
    assert exception_info.value.args[0] == msg

  @pytest.mark.parametrize("feature", ["multimetric", "metric_threshold", "metric_constraint", "search"])
  def test_incorrect_objective_name(self, feature):
    objective_name = "not_a_valid_objective_name"
    experiment_meta = self.get_experiment_feature(feature)
    experiment_meta["metrics"][0]["objective"] = objective_name
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = f"{objective_name} is not one of the allowed values: maximize, minimize"
    assert exception_info.value.args[0] == msg