# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from sigoptaux.adapter_info_containers import DomainInfo
from sigoptaux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)
from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.models import dataclass_to_dict
from sigoptlite.sources import BaseOptimizationSource
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import (
  DEFAULT_METRICS,
  DEFAULT_METRICS_MULTIPLE,
  DEFAULT_PARAMETERS,
  EXPERIMENT_META_WITH_CONSTRAINTS,
  PARAMETER_BETA_PRIOR,
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  PARAMETER_NORMAL_PRIOR,
)


class TestAdapter(UnitTestsBase):
  @pytest.fixture
  def experiment(self):
    experiment_meta = dict(
      parameters=[
        PARAMETER_DOUBLE,
        PARAMETER_INT,
        PARAMETER_CATEGORICAL,
      ],
      metrics=DEFAULT_METRICS_MULTIPLE,
      observation_budget=50,
    )
    return LocalExperimentBuilder(experiment_meta)

  def test_observations_to_points(self, experiment):
    observations = [
      self.make_observation(
        assignments={"d1": 5.5, "i1": 15, "c1": "e"},
        values=[dict(name="y1", value=1.1), dict(name="y2", value=2.2)],
      ),
      self.make_observation(
        assignments={"d1": 7.5, "i1": 18, "c1": "a"}, values=[dict(name="y1", value=3.3), dict(name="y2", value=4.4)]
      ),
    ]
    adapter = BaseOptimizationSource(experiment)
    points_container = adapter.make_points_sampled(experiment, observations)
    expected_points = numpy.array(
      [
        [5.5, 15, 5],
        [7.5, 18, 1],
      ]
    )
    assert numpy.all(points_container.points == expected_points)
    expected_values = numpy.array(
      [
        [1.1, 2.2],
        [3.3, 4.4],
      ]
    )
    assert numpy.all(points_container.values == expected_values)
    expected_value_vars = numpy.zeros((2, 2))
    assert numpy.all(points_container.value_vars == expected_value_vars)
    assert numpy.all(points_container.failures == numpy.array([False] * 2))

  def test_observations_to_points_with_variance(self, experiment):
    observations = [
      self.make_observation(
        assignments={"d1": 5.5, "i1": 15, "c1": "e"},
        values=[
          dict(name="y1", value=1.1, value_stddev=1e-1),
          dict(name="y2", value=2.2, value_stddev=1e-2),
        ],
      ),
      self.make_observation(
        assignments={"d1": 7.5, "i1": 18, "c1": "a"},
        values=[
          dict(name="y1", value=3.3, value_stddev=1e-3),
          dict(name="y2", value=4.4, value_stddev=1e-4),
        ],
      ),
    ]
    adapter = BaseOptimizationSource(experiment)
    points_container = adapter.make_points_sampled(experiment, observations)
    expected_value_vars = numpy.array(
      [
        [1e-1, 1e-2],
        [1e-3, 1e-4],
      ]
    )
    assert numpy.all(points_container.value_vars == expected_value_vars)

  def test_observations_to_points_with_failures(self, experiment):
    observations = [
      self.make_observation(
        assignments={"d1": 5.5, "i1": 15, "c1": "e"},
        failed=True,
      ),
      self.make_observation(
        assignments={"d1": 7.5, "i1": 18, "c1": "a"},
        failed=True,
      ),
    ]
    adapter = BaseOptimizationSource(experiment)
    points_container = adapter.make_points_sampled(experiment, observations)
    assert numpy.all(points_container.failures == numpy.array([True] * 2))

  def test_observations_with_task(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = [
      self.make_observation(
        assignments={"d1": 5.5, "l1": 1, "i1": 15, "c1": "e", "g1": 0.3},
        values=[dict(name="y1", value=1.1)],
        task={"name": "cheap", "cost": 0.1},
      ),
      self.make_observation(
        assignments={"d1": 7.5, "l1": 1, "i1": 18, "c1": "a", "g1": 0.1},
        values=[dict(name="y1", value=3.3)],
        task={"name": "expensive", "cost": 1},
      ),
    ]
    adapter = BaseOptimizationSource(experiment)
    points_container = adapter.make_points_sampled(experiment, observations)
    expected_task_costs = numpy.array([0.1, 1])
    assert len(points_container.task_costs) == 2
    assert numpy.all(points_container.task_costs == expected_task_costs)


class TestGenerateDomainInfo(UnitTestsBase):
  def test_generate_domain_info(self):
    experiment_meta = dict(
      parameters=DEFAULT_PARAMETERS,
      metrics=DEFAULT_METRICS,
    )
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    domain_info = adapter.form_domain_info(local_experiment)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5, 0]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [10, 20]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3, 4, 5]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.01, 0.1, 0.3, 0.9]},
      ],
      force_hitandrun_sampling=False,
      priors=None,
    )
    assert domain_info == expected_domain_info

  def test_generate_domain_info_priors(self):
    experiment_meta_with_priors = dict(
      parameters=[
        PARAMETER_NORMAL_PRIOR,
        PARAMETER_BETA_PRIOR,
        PARAMETER_DOUBLE,
      ],
      metrics=DEFAULT_METRICS,
    )
    local_experiment = LocalExperimentBuilder(experiment_meta_with_priors)
    adapter = BaseOptimizationSource(local_experiment)
    domain_info = adapter.form_domain_info(local_experiment)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      ],
      force_hitandrun_sampling=False,
      priors=[
        {"name": ParameterPriorNames.NORMAL, "params": {"mean": 5, "scale": 2}},
        {"name": ParameterPriorNames.BETA, "params": {"shape_a": 1, "shape_b": 10}},
        {"name": None, "params": None},
      ],
    )
    assert domain_info == expected_domain_info

  def test_generate_domain_info_constraints(self):
    local_experiment = LocalExperimentBuilder(EXPERIMENT_META_WITH_CONSTRAINTS)
    adapter = BaseOptimizationSource(local_experiment)
    domain_info = adapter.form_domain_info(local_experiment)
    expected_domain_info = DomainInfo(
      constraint_list=[
        {"weights": [1, 0, 2, 0, 0, 0], "rhs": 0.5, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, -3, 0, -4, 0, 0], "rhs": -0.9, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 1, 1], "rhs": 10, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      ],
      force_hitandrun_sampling=True,
      priors=None,
    )
    assert domain_info == expected_domain_info


class TestFormMetricsInfo(UnitTestsBase):
  def get_points_sampled(self, experiment, num_observations):
    observations = self.make_random_observations(experiment, num_observations)
    points_sampled = BaseOptimizationSource.make_points_sampled(experiment, observations)
    return points_sampled

  def test_form_metrics_info_single(self):
    experiment_meta = self.get_experiment_feature("default")
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment)
    assert not metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 100
    assert metrics_info.user_specified_thresholds == [None]
    assert not metrics_info.has_optimized_metric_thresholds
    assert not metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize"]
    assert metrics_info.optimized_metrics_index == [0]
    assert metrics_info.constraint_metrics_index == []
    assert metrics_info.has_optimization_metrics

  def test_form_metrics_info_multi(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment)
    assert metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 32
    assert metrics_info.user_specified_thresholds == [None, None]
    assert not metrics_info.has_optimized_metric_thresholds
    assert not metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize", "minimize"]
    assert metrics_info.optimized_metrics_index == [0, 1]
    assert metrics_info.constraint_metrics_index == []
    assert metrics_info.has_optimization_metrics

  def test_form_metrics_info_metric_thresholds(self):
    experiment_meta = self.get_experiment_feature("metric_threshold")
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment)
    assert metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 321
    assert metrics_info.user_specified_thresholds == [0.5, None]
    assert metrics_info.has_optimized_metric_thresholds
    assert not metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize", "minimize"]
    assert metrics_info.optimized_metrics_index == [0, 1]
    assert metrics_info.constraint_metrics_index == []
    assert metrics_info.has_optimization_metrics

  def test_form_metrics_info_one_constraint(self):
    experiment_meta = self.get_experiment_feature("metric_constraint")
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment)
    assert not metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 512
    assert metrics_info.user_specified_thresholds == [0.5, None]
    assert not metrics_info.has_optimized_metric_thresholds
    assert metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize", "minimize"]
    assert metrics_info.optimized_metrics_index == [1]
    assert metrics_info.constraint_metrics_index == [0]
    assert metrics_info.has_optimization_metrics

  def test_form_metrics_info_search(self):
    experiment_meta = self.get_experiment_feature("search")
    local_experiment = LocalExperimentBuilder(experiment_meta)
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment)
    assert not metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 97
    assert metrics_info.user_specified_thresholds == [0.25, 0.75]
    assert not metrics_info.has_optimized_metric_thresholds
    assert metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize", "minimize"]
    assert metrics_info.optimized_metrics_index == []
    assert metrics_info.constraint_metrics_index == [0, 1]
    assert not metrics_info.has_optimization_metrics

  @pytest.mark.parametrize("objective", ["maximize", "minimize"])
  def test_form_metrics_info_multisolution_experiment(self, objective):
    experiment_meta = self.get_experiment_feature("multisolution")
    experiment_meta["metrics"][0]["objective"] = objective
    local_experiment = LocalExperimentBuilder(experiment_meta)
    num_observations = 11
    points_sampled = self.get_points_sampled(local_experiment, num_observations)
    quantile = MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD
    if objective == "minimize":
      quantile = 1 - quantile
    expected_threshold = numpy.quantile(
      points_sampled.values[~points_sampled.failures, 0],
      quantile,
    )
    adapter = BaseOptimizationSource(local_experiment)
    metrics_info = adapter.form_metrics_info(local_experiment, points_sampled)
    assert metrics_info.observation_budget == 111
    assert metrics_info.user_specified_thresholds == [expected_threshold]
    assert metrics_info.optimized_metrics_index == []
    assert metrics_info.objectives == [objective]
    assert metrics_info.constraint_metrics_index == [0]
    assert not metrics_info.has_optimized_metric_thresholds
    assert metrics_info.has_constraint_metrics


class TestConditionals(UnitTestsBase):
  def assert_parameter_list_are_equal(self, original_list, condional_list):
    assert len(original_list) == len(condional_list)
    for org_param, cond_param in zip(original_list, condional_list):
      orginal_dict, condional_dict = dataclass_to_dict(org_param), dataclass_to_dict(cond_param)
      orginal_dict["conditions"] = []
      assert orginal_dict == condional_dict

  def test_create_unconditioned_experiment_from_conditionals(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    original_experiment = LocalExperimentBuilder(experiment_meta)
    unconditioned_exp = BaseOptimizationSource.apply_conditional_transformation_to_experiment(original_experiment)
    assert [p.name for p in unconditioned_exp.parameters] == ["a", "b", "c", "x"]
    self.assert_parameter_list_are_equal(original_experiment.parameters, unconditioned_exp.parameters[:-1])
    assert all(not bool(p.conditions) for p in unconditioned_exp.parameters)
    domain_info = BaseOptimizationSource.form_domain_info(unconditioned_exp)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 50]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-50, 0]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ],
      force_hitandrun_sampling=False,
      priors=None,
    )
    assert domain_info == expected_domain_info
    base_source = BaseOptimizationSource(original_experiment)
    assert base_source.experiment == unconditioned_exp
    assert base_source.form_domain_info(base_source.experiment) == expected_domain_info

  def test_create_unconditioned_experiment_from_multiconditional(self):
    experiment_meta = self.get_experiment_feature("multiconditional")
    original_experiment = LocalExperimentBuilder(experiment_meta)
    unconditioned_exp = BaseOptimizationSource.apply_conditional_transformation_to_experiment(original_experiment)
    assert [p.name for p in unconditioned_exp.parameters] == ["a", "b", "c", "d", "x", "y", "z"]
    self.assert_parameter_list_are_equal(original_experiment.parameters, unconditioned_exp.parameters[:-3])
    assert all(not bool(p.conditions) for p in unconditioned_exp.parameters)
    domain_info = BaseOptimizationSource.form_domain_info(unconditioned_exp)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 50]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-50, 0]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
      ],
      force_hitandrun_sampling=False,
      priors=None,
    )
    assert domain_info == expected_domain_info
    base_source = BaseOptimizationSource(original_experiment)
    assert base_source.experiment == unconditioned_exp
    assert base_source.form_domain_info(base_source.experiment) == expected_domain_info

  @pytest.mark.parametrize(
    "unconditioned_assignments,expected_assignments",
    [
      (dict(a=1, b=-50.0, c="d", x="1"), dict(a=1, x="1")),
      (dict(a=1, b=-50.0, c="d", x="5"), dict(a=1, b=-50.0, x="5")),
      (dict(a=1, b=-50.0, c="d", x="10"), dict(a=1, b=-50.0, c="d", x="10")),
    ],
  )
  def test_unconditioned_suggestions_from_conditionals(self, unconditioned_assignments, expected_assignments):
    experiment_meta = self.get_experiment_feature("conditionals")
    original_experiment = LocalExperimentBuilder(experiment_meta)
    base_source = BaseOptimizationSource(original_experiment)
    # pylint: disable=protected-access
    assert base_source._original_experiment == original_experiment
    assert base_source._original_experiment.is_conditional
    # pylint: enable=protected-access
    assert not base_source.experiment.is_conditional
    unconditioned_suggestion = self.make_suggestion(assignments=unconditioned_assignments)
    suggestion = base_source.remove_transformations_from_source_suggestion(unconditioned_suggestion)
    assert suggestion.assignments == expected_assignments
