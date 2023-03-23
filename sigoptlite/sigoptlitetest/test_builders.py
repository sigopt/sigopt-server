# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import pytest

from sigoptlite.builders import *
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import PARAMETER_CATEGORICAL, PARAMETER_INT


class TestLocalExperimentBuilder(UnitTestsBase):
  def test_parameters_are_unique(self):
    experiment_meta = self.get_experiment_feature("default")
    # experiment_meta has at least three parameters for this test
    assert len(experiment_meta["parameters"]) >= 3
    experiment_meta["parameters"][-2] = experiment_meta["parameters"][0]
    with pytest.raises(ValueError):
      LocalExperimentBuilder(experiment_meta)

  def test_metrics_are_unique(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["metrics"][-1] = experiment_meta["metrics"][0]
    with pytest.raises(ValueError):
      LocalExperimentBuilder(experiment_meta)

  def test_conditionals_satisfy_values(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["metrics"][-1] = experiment_meta["metrics"][0]
    with pytest.raises(ValueError):
      LocalExperimentBuilder(experiment_meta)


class TestLocalParameterBuilder(UnitTestsBase):
  @pytest.fixture
  def valid_categorical_input_dict(self):
    return {
      "name": "c",
      "type": "categorical",
      "bounds": None,
      "categorical_values": ["a", "b"],
      "conditions": [],
      "grid": [],
      "prior": None,
      "transformation": None,
    }

  def test_non_categorical_creation(self):
    input_dict = {
      "name": "c",
      "type": "int",
      "bounds": {"min": 0, "max": 10},
      "categorical_values": [],
      "conditions": [],
      "grid": [],
      "prior": None,
      "transformation": None,
    }
    optional_fields = ["categorical_values", "conditions", "grid", "prior", "transformation"]
    field_to_remove = random.choice(optional_fields)
    input_dict.pop(field_to_remove)
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.name == input_dict["name"]
    assert parameter.type == input_dict["type"]
    assert len(parameter.categorical_values) == 0
    assert parameter.bounds.min == input_dict["bounds"]["min"]
    assert parameter.bounds.max == input_dict["bounds"]["max"]
    assert len(parameter.conditions) == 0
    assert len(parameter.grid) == 0
    assert parameter.prior is None
    assert parameter.transformation is None

  @pytest.mark.parametrize(
    "categorical_values",
    [
      ["b", "a"],
      [{"enum_index": 8, "name": "a"}, {"enum_index": 9, "name": "b"}],
      [{"enum_index": -1, "name": "a"}, {"name": "b"}],
      [{"enum_index": 1, "name": "b"}, {"enum_index": 2, "name": "a"}],
      [{"name": "a"}, {"name": "b"}],
      [{"name": "b"}, {"name": "a"}],
    ],
  )
  def test_categorical_creation(self, valid_categorical_input_dict, categorical_values):
    cat_names = ["a", "b"]
    input_dict = dict(valid_categorical_input_dict)
    input_dict["categorical_values"] = categorical_values
    optional_fields = ["bounds", "conditions", "grid", "prior", "transformation"]
    field_to_remove = random.choice(optional_fields)
    input_dict.pop(field_to_remove)
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.name == input_dict["name"]
    assert parameter.type == input_dict["type"]
    for i, (cv, cat_name) in enumerate(zip(parameter.categorical_values, cat_names)):
      assert cv.enum_index == (i + 1)
      assert cv.name == cat_name
    assert parameter.bounds is None
    assert len(parameter.conditions) == 0
    assert len(parameter.grid) == 0
    assert parameter.prior is None
    assert parameter.transformation is None

  def test_categorical_bounds_incompatible(self, valid_categorical_input_dict):
    input_dict = dict(valid_categorical_input_dict)
    input_dict["bounds"] = {"min": 1e-6, "max": 1}
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  def test_categorical_grid_incompatible(self, valid_categorical_input_dict):
    input_dict = dict(valid_categorical_input_dict)
    input_dict["grid"] = [0, 1]
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  @pytest.mark.parametrize("transformation", [None, "log"])
  def test_parameter_double_grid(self, transformation):
    input_dict = {
      "name": "g",
      "type": "double",
      "grid": [0.0001, 0.001, 0.33, 0.99],
      "transformation": transformation,
    }
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.grid == [0.0001, 0.001, 0.33, 0.99]
    assert parameter.bounds is None
    assert parameter.transformation is transformation
    assert not parameter.has_prior

  def test_parameter_int_grid(self):
    input_dict = {
      "name": "g",
      "type": "int",
      "grid": [2, 3, 4],
    }
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.grid == [2, 3, 4]
    assert parameter.bounds is None
    assert parameter.transformation is None
    assert not parameter.has_prior

  @pytest.mark.parametrize("param_type", ["int", "double"])
  def test_parameter_grid_single_value_incompatible(self, param_type):
    input_dict = {
      "name": "g",
      "type": param_type,
      "grid": [1.0],
    }
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  def test_parameter_log_transformation(self):
    input_dict = {
      "name": "l",
      "type": "double",
      "bounds": {"min": 1e-6, "max": 1},
      "transformation": "log",
    }
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.has_transformation

  @pytest.mark.parametrize("min_value", [-10, -1, 0])
  def test_parameter_log_transformation_bounds_incompatible(self, min_value):
    input_dict = {
      "name": "l",
      "type": "double",
      "bounds": {"min": min_value, "max": 1},
      "transformation": "log",
    }
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  @pytest.mark.parametrize("param_dict", [PARAMETER_INT, PARAMETER_CATEGORICAL])
  def test_parameter_log_transformation_parameter_incompatible(self, param_dict):
    input_dict = dict(param_dict)
    input_dict["transformation"] = "log"
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  @pytest.mark.parametrize("min_value", [-10, -1, 0])
  def test_parameter_grid_log_non_positive_values_incompatible(self, min_value):
    input_dict = {
      "name": "g",
      "type": "double",
      "grid": [1, min_value],
      "transformation": "log",
    }
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  @pytest.mark.parametrize("valid_mean", [-1, -0.1, 0, 0.1, 1])
  def test_parameter_with_normal_prior(self, valid_mean):
    input_dict = {
      "name": "a",
      "type": "double",
      "bounds": {"min": -1, "max": 1},
      "prior": {"name": "normal", "mean": valid_mean, "scale": 0.01},
    }
    parameter = LocalParameterBuilder(input_dict)
    assert parameter.has_prior
    assert parameter.prior.is_normal
    assert parameter.bounds.is_value_within(parameter.prior.mean)

  @pytest.mark.parametrize("bad_mean", [-2, 2, None])
  def test_parameter_with_normal_prior_incompatible(self, bad_mean):
    input_dict = {
      "name": "a",
      "type": "double",
      "bounds": {"min": -1, "max": 1},
      "prior": {"name": "normal", "mean": bad_mean, "scale": 0.01},
    }
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)

  @pytest.mark.parametrize("param_dict", [PARAMETER_INT, PARAMETER_CATEGORICAL])
  def test_parameter_with_prior_incompatible(self, param_dict):
    input_dict = dict(param_dict)
    input_dict["prior"] = {"name": "normal", "mean": 0.1, "scale": 0.01}
    with pytest.raises(ValueError):
      LocalParameterBuilder(input_dict)


class TestLocalConditionalBuilder(UnitTestsBase):
  @pytest.mark.parametrize(
    "conditional_values",
    [
      ["b", "a"],
      ["a", "b"],
    ],
  )
  def test_create_local_conditional(self, conditional_values):
    input_dict = dict(name="x", values=conditional_values)
    conditional = LocalConditionalBuilder(input_dict)
    assert input_dict["name"] == conditional.name
    for i, (cv, cond_name) in enumerate(zip(conditional.values, conditional_values)):
      assert cv.enum_index == (i + 1)
      assert cv.name == cond_name


class TestLocalMetricBuilder(UnitTestsBase):
  def test_create_local_metric(self):
    input_dict = {
      "name": "maximize",
      "objective": "optimize",
      "strategy": None,
    }
    metric = LocalMetricBuilder(input_dict)
    assert metric.name == input_dict["name"]
    assert metric.objective == input_dict["objective"]
    assert metric.strategy == input_dict["strategy"]
    assert not metric.threshold


class TestLocalTaskBuilder(UnitTestsBase):
  def test_create_local_task(self):
    input_dict = {
      "name": "cheap",
      "cost": 0.1,
    }
    metric = LocalTaskBuilder(input_dict)
    assert metric.name == input_dict["name"]
    assert metric.cost == input_dict["cost"]

  @pytest.mark.parametrize("bad_cost", [-1, 0])
  def test_create_local_task_incompatible(self, bad_cost):
    input_dict = {
      "name": "bad_task",
      "cost": bad_cost,
    }
    with pytest.raises(ValueError):
      LocalTaskBuilder(input_dict)


class TestLocalBuilder(UnitTestsBase):
  def test_create_local_bounds(self):
    random_min_value = random.choice([-1, 0.5, 2])
    input_dict = {
      "min": random_min_value,
      "max": random_min_value + 0.1,
    }
    bounds = LocalBoundsBuilder(input_dict)
    assert bounds.min == input_dict["min"]
    assert bounds.max == input_dict["max"]

  def test_incompatible_local_bounds(self):
    input_dict = {
      "min": 2,
      "max": 1,
    }
    with pytest.raises(ValueError):
      LocalBoundsBuilder(input_dict)


class TestLocalParameterPriorBuilder(UnitTestsBase):
  def test_create_local_parameter_prior_beta(self):
    input_dict = {
      "name": "beta",
      "shape_a": 2,
      "shape_b": 4.5,
    }
    prior = LocalParameterPriorBuilder(input_dict)
    assert prior.shape_a == input_dict["shape_a"]
    assert prior.shape_b == input_dict["shape_b"]
    assert prior.mean is None
    assert prior.scale is None

  @pytest.mark.parametrize("bad_value", [-1, 0, None])
  def test_incompatible_local_parameter_prior_beta(self, bad_value):
    input_dict = {
      "name": "beta",
      "shape_a": -1,
      "shape_b": 4.5,
    }
    field = random.choice(["shape_a", "shape_b"])
    input_dict[field] = bad_value
    with pytest.raises(ValueError):
      LocalParameterPriorBuilder(input_dict)

  def test_create_local_parameter_prior_normal(self):
    input_dict = {
      "name": "normal",
      "mean": 0.6,
      "scale": 0.15,
    }
    prior = LocalParameterPriorBuilder(input_dict)
    assert prior.shape_a is None
    assert prior.shape_b is None
    assert prior.mean == input_dict["mean"]
    assert prior.scale == input_dict["scale"]

  @pytest.mark.parametrize("bad_value", [-1, 0, None])
  def test_incompatible_local_parameter_prior_normal(self, bad_value):
    input_dict = {
      "name": "normal",
      "mean": 2,
      "scale": bad_value,
    }
    with pytest.raises(ValueError):
      LocalParameterPriorBuilder(input_dict)
