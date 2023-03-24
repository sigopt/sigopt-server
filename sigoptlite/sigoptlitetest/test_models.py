# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.models import LocalSuggestion
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_METRICS_SEARCH


class LocalExperimentBase(UnitTestsBase):
  def check_experiment_parameters(self, meta, experiment):
    for param_dict, param in zip(meta["parameters"], experiment.parameters):
      assert param_dict["name"] == param.name
      assert param_dict["type"] == param.type
      param_bounds = param_dict.get("bounds")
      if param_bounds:
        assert param_bounds["min"] == param.bounds.min
        assert param_bounds["max"] == param.bounds.max
      else:
        assert not param.bounds
      param_categorical_values = param_dict.get("categorical_values")
      if param_categorical_values:
        if isinstance(param_categorical_values[0], dict):
          get_key = lambda x: x["name"]
        else:
          assert isinstance(param_categorical_values[0], str)
          get_key = lambda x: x
        param_categorical_values = sorted(param_categorical_values, key=get_key)
        for i, cv in enumerate(param.categorical_values):
          assert get_key(param_categorical_values[i]) == cv.name
          assert i == (cv.enum_index - 1)
      else:
        assert not param.categorical_values
      param_grid = param_dict.get("grid")
      if param_grid:
        for grid_value_dict, grid_value in zip(param_grid, param.grid):
          assert grid_value_dict == grid_value
      else:
        assert not param.grid
      assert param_dict.get("transformation") == param.transformation
      param_prior = param_dict.get("prior")
      if param_prior:
        assert param_prior["name"].lower() in ["beta", "normal"]
        if param_prior["name"].lower() == "beta":
          assert param_prior["shape_a"] == param.prior.shape_a
          assert param_prior["shape_b"] == param.prior.shape_b
        if param_prior["name"].lower() == "normal":
          assert param_prior["mean"] == param.prior.mean
          assert param_prior["scale"] == param.prior.scale
      else:
        assert not param.prior

  def check_experiment_metrics(self, meta, experiment):
    optimized_metrics = []
    constraint_metrics = []
    for metric_dict, metric in zip(meta["metrics"], experiment.metrics):
      assert metric_dict["name"] == metric.name
      metric_objective = metric_dict.get("objective", "maximize")
      assert metric_objective == metric.objective
      metric_strategy = metric_dict.get("strategy", "optimize")
      assert metric_strategy == metric.strategy
      metric_threshold = metric_dict.get("threshold")
      assert metric_threshold == metric.threshold
      if metric_strategy == "optimize":
        assert metric.is_optimized
        optimized_metrics.append(metric)
      if metric_strategy == "constraint":
        assert metric.is_constraint
        constraint_metrics.append(metric)
    assert experiment.optimized_metrics == optimized_metrics
    assert experiment.constraint_metrics == constraint_metrics

  def check_experiment_linear_constraints(self, meta, experiment):
    if "linear_constraints" not in meta:
      assert not experiment.linear_constraints
      return
    for constraint_dict, constraint in zip(meta["linear_constraints"], experiment.linear_constraints):
      assert constraint_dict["type"] == constraint.type
      assert constraint_dict["threshold"] == constraint.threshold
      for term_dict, term in zip(constraint_dict["terms"], constraint.terms):
        assert term_dict["name"] == term.name
        assert term_dict["weight"] == term.weight

  def check_experiment_tasks(self, meta, experiment):
    if "tasks" not in meta:
      assert not experiment.is_multitask
      return
    assert experiment.is_multitask
    for task_dict, task in zip(meta["tasks"], experiment.tasks):
      assert task_dict["name"] == task.name
      assert task_dict["cost"] == task.cost

  def check_experiment_conditionals(self, meta, experiment):
    if "conditionals" not in meta:
      assert not experiment.is_conditional
      return
    assert experiment.is_conditional
    for cond_dict, conditional in zip(meta["conditionals"], experiment.conditionals):
      assert cond_dict["name"] == conditional.name
      assert cond_dict["values"] == [cv.name for cv in conditional.values]

  def check_experiment_expected_attributes(self, experiment_meta, experiment):
    self.check_experiment_parameters(experiment_meta, experiment)
    assert experiment.dimension == len(experiment.parameters)
    self.check_experiment_metrics(experiment_meta, experiment)
    num_solutions = experiment_meta.get("num_solutions", 1)
    assert experiment.num_solutions == num_solutions
    if num_solutions > 1:
      assert experiment.is_multisolution
    else:
      assert num_solutions == 1
      assert not experiment.is_multisolution
    self.check_experiment_linear_constraints(experiment_meta, experiment)
    self.check_experiment_tasks(experiment_meta, experiment)
    self.check_experiment_conditionals(experiment_meta, experiment)


class TestLocalExperiment(LocalExperimentBase):
  def test_experiment_with_budget(self, any_meta):
    experiment = LocalExperimentBuilder(any_meta)
    assert experiment.observation_budget > 0
    self.check_experiment_expected_attributes(any_meta, experiment)

  def test_experiment_no_budget(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta.pop("observation_budget")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.observation_budget is None
    assert experiment.num_solutions == 1 and not experiment.is_multisolution
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  @pytest.mark.parametrize("parallel_bandwidth", [-1, 0, 2, 29])
  def test_experiment_parallel_bandwidth_incompatible(self, parallel_bandwidth):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parallel_bandwidth"] = parallel_bandwidth
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    if parallel_bandwidth > 1:
      msg = "sigoptlite experiment must have parallel_bandwidth == 1"
    else:
      msg = ".parallel_bandwidth must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_experiment_with_constraints(self):
    experiment_meta = self.get_experiment_feature("constraints")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.linear_constraints
    assert experiment.observation_budget == 123
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_multimetric_experiment(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert len(experiment.metrics) == 2
    assert experiment.observation_budget == 32
    assert experiment.requires_pareto_frontier_optimization
    assert len(experiment.optimized_metrics) == 2
    assert experiment.optimized_metrics[0].name == "y1"
    assert experiment.optimized_metrics[1].name == "y2"
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_multitask(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.is_multitask
    assert len(experiment.tasks) == 3
    assert [t.name for t in experiment.tasks] == ["cheapest", "cheap", "expensive"]
    assert [t.cost for t in experiment.tasks] == [0.1, 0.5, 1.0]
    assert not experiment.requires_pareto_frontier_optimization
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_multisolution(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.num_solutions == experiment_meta["num_solutions"]
    assert experiment.is_multisolution
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_metric_constraint(self):
    experiment_meta = self.get_experiment_feature("metric_constraint")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert len(experiment.metrics) == 2
    assert not experiment.requires_pareto_frontier_optimization
    assert len(experiment.optimized_metrics) == 1
    assert experiment.optimized_metrics[0].name == "y2"
    assert len(experiment.constraint_metrics) == 1
    assert experiment.constraint_metrics[0].name == "y1"
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_multimetric_experiment_with_threshold(self):
    experiment_meta = self.get_experiment_feature("metric_threshold")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert len(experiment.metrics) == 2
    assert experiment.requires_pareto_frontier_optimization
    assert len(experiment.optimized_metrics) == 2
    assert experiment.optimized_metrics[0].name == "y1"
    assert experiment.optimized_metrics[0].threshold == 0.5
    assert experiment.optimized_metrics[1].name == "y2"
    assert experiment.optimized_metrics[1].threshold is None

    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_with_priors(self):
    experiment_meta = self.get_experiment_feature("priors")
    experiment = LocalExperimentBuilder(experiment_meta)
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_search(self):
    experiment_meta = self.get_experiment_feature("search")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.is_search
    assert len(experiment.metrics) == 2
    assert not experiment.requires_pareto_frontier_optimization
    assert experiment.optimized_metrics == []
    assert len(experiment.constraint_metrics) == 2
    assert experiment.constraint_metrics[0].name == "y1"
    assert experiment.constraint_metrics[1].name == "y2"
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_search_no_budget_incompatible(self):
    experiment_meta = self.get_experiment_feature("search")
    experiment_meta.pop("observation_budget")
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "observation_budget is required for a sigoptlite experiment with constraint metrics"
    assert exception_info.value.args[0] == msg

  def test_experiment_conditionals_search_incompatible(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    experiment_meta["metrics"] = DEFAULT_METRICS_SEARCH
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "All-Constraint sigoptlite experiment does not support conditional parameters"
    assert exception_info.value.args[0] == msg

  def test_experiment_conditionals(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.observation_budget == 30
    assert experiment.is_conditional
    assert len(experiment.conditionals) == 1
    conditional = experiment.conditionals[0]
    assert conditional.name == "x"
    assert [v.name for v in conditional.values] == ["1", "5", "10"]

  def test_experiment_multiconditional(self):
    experiment_meta = self.get_experiment_feature("multiconditional")
    experiment = LocalExperimentBuilder(experiment_meta)
    assert experiment.observation_budget == 37
    assert experiment.is_conditional
    assert [c.name for c in experiment.conditionals] == ["x", "y", "z"]
    assert [v.name for v in experiment.conditionals[0].values] == ["x1", "x2"]
    assert [v.name for v in experiment.conditionals[1].values] == ["y1", "y2", "y3"]
    assert [v.name for v in experiment.conditionals[2].values] == ["on", "off"]
    self.check_experiment_expected_attributes(experiment_meta, experiment)

  def test_experiment_missing_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["parameters"]
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "Missing required json key `parameters` in sigoptlite experiment:"
    assert exception_info.value.args[0].startswith(msg)

  def test_experiment_parameters_empty_list(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parameters"] = []
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "The length of .parameters must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_experiment_missing_metrics(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["metrics"]
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "Missing required json key `metrics` in sigoptlite experiment:"
    assert exception_info.value.args[0].startswith(msg)

  def test_experiment_metrics_empty_list(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = []
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "The length of .metrics must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_experiment_bad_structure(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["name"] = 12
    with pytest.raises(ValueError) as exception_info:
      LocalExperimentBuilder(experiment_meta)
    msg = "Invalid type for .name, expected type string"
    assert exception_info.value.args[0] == msg


class TestLocalParameters(UnitTestsBase):
  @pytest.mark.parametrize(
    "categorical_values,expected_values",
    [
      (["p1", "p0"], ["p0", "p1"]),
      (["x3", "x2", "x1"], ["x1", "x2", "x3"]),
      (["d", "z", "a"], ["a", "d", "z"]),
      ([{"name": "c"}, {"name": "b"}, {"name": "a"}], ["a", "b", "c"]),
      ([{"name": "p0"}, {"name": "p1"}, {"name": "p2"}], ["p0", "p1", "p2"]),
    ],
  )
  def test_sorted_categorical_parameter(self, experiment_meta, categorical_values, expected_values):
    categorical_param_dict = dict(
      name="cat_a",
      type="categorical",
      categorical_values=categorical_values,
    )
    experiment_meta["parameters"][0] = categorical_param_dict
    experiment = LocalExperimentBuilder(experiment_meta)
    categorical_param = experiment.parameters[0]
    assert categorical_param.name == "cat_a"
    for i, cv in enumerate(categorical_param.categorical_values):
      assert cv.name == expected_values[i]
      assert cv.enum_index == i + 1


class TestLocalSuggestions(UnitTestsBase):
  @pytest.fixture
  def exp_no_conditionals(self):
    meta = dict(
      name="no-conditinal",
      parameters=[
        dict(name="a", type="int", bounds=dict(min=0, max=1)),
        dict(name="b", type="int", bounds=dict(min=0, max=1)),
        dict(name="c", type="int", bounds=dict(min=0, max=1)),
      ],
      metrics=[dict(name="metric")],
      observation_budget=1,
    )
    experiment = LocalExperimentBuilder(meta)
    return experiment

  @pytest.fixture
  def exp_conditionals(self):
    meta = dict(
      name="conditionals",
      conditionals=[
        dict(name="x", values=["1", "2", "3"]),
        dict(name="y", values=["1", "2"]),
      ],
      parameters=[
        dict(
          name="a",
          type="int",
          bounds=dict(min=0, max=1),
          conditions=dict(x=["1"]),
        ),
        dict(
          name="b",
          type="int",
          bounds=dict(min=0, max=1),
          conditions=dict(x=["1", "2"], y=["2"]),
        ),
        dict(
          name="c",
          type="int",
          bounds=dict(min=0, max=1),
        ),
      ],
      metrics=[dict(name="metric")],
      observation_budget=1,
    )
    experiment = LocalExperimentBuilder(meta)
    return experiment

  @pytest.mark.parametrize(
    "test,expected",
    [
      (dict(x="1", y="1", a=0, b=0, c=0), dict(x="1", y="1", a=0, c=0)),
      (dict(x="1", y="2", a=0, b=0, c=0), dict(x="1", y="2", a=0, b=0, c=0)),
      (dict(x="2", y="1", a=0, b=0, c=0), dict(x="2", y="1", c=0)),
      (dict(x="2", y="2", a=0, b=0, c=0), dict(x="2", y="2", b=0, c=0)),
      (dict(x="3", y="1", a=0, b=0, c=0), dict(x="3", y="1", c=0)),
      (dict(x="3", y="2", a=0, b=0, c=0), dict(x="3", y="2", c=0)),
    ],
  )
  def test_get_assignments_with_conditionals(self, test, expected, exp_conditionals):
    suggestion = LocalSuggestion(assignments=test)
    assert suggestion.get_assignments(exp_conditionals) == expected

  @pytest.mark.parametrize(
    "test",
    [
      (dict(x=1, y=1, a=0, b=0, c=0)),
      (dict(x=1, y=2, a=0, b=0, c=0)),
      (dict(x=2, y=1, a=0, b=0, c=0)),
      (dict(x=2, y=2, a=0, b=0, c=0)),
      (dict(x=3, y=1, a=0, b=0, c=0)),
      (dict(x=3, y=2, a=0, b=0, c=0)),
    ],
  )
  def test_get_assignments_without_conditionals(self, test, exp_no_conditionals):
    suggestion = LocalSuggestion(assignments=test)
    assert suggestion.get_assignments(exp_no_conditionals) == dict(a=0, b=0, c=0)
