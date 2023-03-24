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
    experiment_meta["metrics"].append({"name": "f3", "strategy": "optimize", "objective": "minimize"})
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

  @pytest.mark.parametrize("feature", ["multimetric", "metric_threshold", "search"])
  def test_multimetric_and_multisolution_incompatible(self, feature):
    experiment_meta = self.get_experiment_feature(feature)
    experiment_meta["num_solutions"] = 5
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment with multiple solutions require exactly one optimized metric"
    assert exception_info.value.args[0] == msg

  @pytest.mark.parametrize("feature", ["multimetric", "metric_threshold"])
  def test_multimetric_and_multitask_incompatible(self, feature):
    experiment_meta = self.get_experiment_feature(feature)
    experiment_meta["tasks"] = DEFAULT_TASKS
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment cannot have both tasks and multiple optimized metrics"
    assert exception_info.value.args[0] == msg

  @pytest.mark.parametrize("feature", ["metric_constraint", "search"])
  def test_metric_constraint_and_multitask_incompatible(self, feature):
    experiment_meta = self.get_experiment_feature(feature)
    experiment_meta["tasks"] = DEFAULT_TASKS
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "sigoptlite experiment cannot have both tasks and constraint metrics"
    assert exception_info.value.args[0] == msg

  def test_duplicate_metrics(self, experiment_meta):
    metric_name = "duplicated_metric"
    experiment_meta["metrics"] = [dict(name=metric_name, objective="maximize", strategy="optimize")] * 2
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = f"No duplicate metrics are allowed: {[metric_name, metric_name]}"
    assert exception_info.value.args[0] == msg

  @pytest.mark.parametrize("feature", ["multimetric", "metric_threshold", "metric_constraint", "search"])
  def test_missing_objective_defaults_to_maximization(self, feature):
    experiment_meta = self.get_experiment_feature(feature)
    del experiment_meta["metrics"][0]["objective"]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].objective == "maximize"


class TestMultimetricThresholdExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  def test_single_metric_threshold_for_optimization_not_allowed(self, experiment_meta):
    experiment_meta["metrics"] = [dict(name="y1", objective="maximize", threshold=0.5, strategy="optimize")]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = (
      "Thresholds are only supported for experiments with more than one optimized metric. Try an All-Constraint"
      " experiment instead by setting `strategy` to `constraint`."
    )
    assert exception_info.value.args[0] == msg

  def test_single_metric_threshold_for_constraint_is_allowed(self, experiment_meta):
    experiment_meta["metrics"] = [dict(name="y1", objective="maximize", threshold=0.5, strategy="constraint")]
    self.conn.experiments().create(**experiment_meta)


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
