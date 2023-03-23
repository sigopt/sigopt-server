# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from sigopt import Connection
from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_TASKS


class TestMultimetricExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("multimetric")

  def test_more_than_two_optimized_metrics_forbidden(self, experiment_meta):
    experiment_meta["metrics"].append(
      {"name": "f3", "strategy": "optimize", "objective": "minimize"}
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment must have one or two optimized metrics"
    assert exception_info.value.args[0] == msg

  def test_multimetric_experiment_no_budget_forbidden(self, experiment_meta):
    experiment_meta.pop("observation_budget")
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with more than one optimized metric"
    assert exception_info.value.args[0] == msg

  def test_multimetric_and_multisolution_incompatible(self, experiment_meta):
    experiment_meta["num_solutions"] = 5
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment with multiple solutions require exactly one optimized metric"
    assert exception_info.value.args[0] == msg

  def test_multimetric_and_multitask_incompatible(self, experiment_meta):
    experiment_meta["tasks"] = DEFAULT_TASKS
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment cannot have both tasks and multiple optimized metrics"
    assert exception_info.value.args[0] == msg


class TestMetricConstraintExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("metric_constraint")

  def test_metric_constraint_and_multitask_incompatible(self, experiment_meta):
    experiment_meta["tasks"] = DEFAULT_TASKS
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment cannot have both tasks and constraint metrics"
    assert exception_info.value.args[0] == msg

  def test_metric_constraint_no_budget_forbidden(self, experiment_meta):
    experiment_meta.pop("observation_budget")
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with constraint metrics"
    assert exception_info.value.args[0] == msg

  def test_constraint_metric_no_threshold_forbidden(self, experiment_meta):
    experiment_meta["metrics"] = [
      dict(
        name="y1",
        objective="maximize",
        strategy="constraint",
      ),
      dict(
        name="y2",
        objective="minimize",
        strategy="optimize",
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "Constraint metrics must have the threshold field defined"
    assert exception_info.value.args[0] == msg
