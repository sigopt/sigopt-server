# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlite.models import FIXED_EXPERIMENT_ID
from sigoptlitetest.endpoints.base_test import UnitTestsEndpoint
from sigoptlitetest.constants import PARAMETER_INT, PARAMETER_CATEGORICAL, PARAMETER_BETA_PRIOR

class TestExperimentBasic(UnitTestsEndpoint):
  def test_create_and_fetch(self, any_meta):
    experiment = self.conn.experiments().create(**any_meta)
    assert experiment.id is not None

    experiment_fetched = self.conn.experiments(experiment.id).fetch()
    assert experiment == experiment_fetched

  def test_no_observation_budget(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["observation_budget"]
    experiment = self.conn.experiments().create(**experiment_meta)
    assert experiment.observation_budget is None

  # TODO: need a much more descriptive error when user tries to do this
  def test_other_endpoint_before_experiment_create(self):
    conn = Connection(driver=LocalDriver)
    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).fetch()

    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).suggestions().create()

    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).observations().create(suggestion=1, values={"name": "y", "value": 1})

    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).observations().fetch()

    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).observations().fetch()

    with pytest.raises(Exception):
      conn.experiments(FIXED_EXPERIMENT_ID).best_assignments().fetch()


class TestExperimentParameters(UnitTestsEndpoint):
  @pytest.mark.xfail  # Not being handled property atm
  def test_no_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["parameters"]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_empty_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parameters"] = []
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_duplicate_parameters(self):
    parameter = dict(name="c", type="categorical", categorical_values=["d", "e"])
    with pytest.raises(ValueError):
      self.conn.experiments().create(
        parameters=[parameter] * 2,
        metrics=[dict(name="y1", objective="maximize", strategy="optimize")],
      )

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_experiment_create_extra_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    with pytest.raises(ValueError):
      self.conn.experiments().create(not_real_experiment_meta_parameter=3.1415, **experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_experiment_create_wrong_parameter_types(self, any_meta):
    any_meta["parameters"][0]["type"] = "invalid_type"
    with pytest.raises(ValueError):
      self.conn.experiments().create(**any_meta)

  @pytest.mark.parametrize(
    "categorical_values",
    [["d", "e"], [dict(name="d"), dict(name="e")], [dict(name="d", enum_index=1), dict(name="e", enum_index=2)]],
  )
  def test_categorical_proper_enum_index(self, categorical_values):
    e = self.conn.experiments().create(
      parameters=[dict(name="c", type="categorical", categorical_values=["d", "e"])],
      metrics=[dict(name="y1", objective="maximize", strategy="optimize")],
    )
    (p,) = e.parameters
    (cat1, cat2) = p.categorical_values
    assert cat1.enum_index == 1
    assert cat1.name == "d"
    assert cat2.enum_index == 2
    assert cat2.name == "e"

  def test_create_with_correct_parameter_priors(self):
    experiment_meta = self.get_experiment_feature("priors")
    e = self.conn.experiments().create(**experiment_meta)
    parameter_normal = e.parameters[1]
    assert parameter_normal.prior is not None
    assert parameter_normal.prior.mean == 5.0
    assert parameter_normal.prior.scale == 2.0
    assert parameter_normal.prior.shape_a is None
    assert parameter_normal.prior.shape_b is None

    parameter_beta = e.parameters[5]
    assert parameter_beta.prior is not None
    assert parameter_beta.prior.shape_a == 1
    assert parameter_beta.prior.shape_b == 10
    assert parameter_beta.prior.mean is None
    assert parameter_beta.prior.scale is None

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  @pytest.mark.parametrize("scale", [0, -1, -10])
  def test_create_with_incorrect_normal_prior(self, scale):
    parameter_normal = dict(
      name="parameter_normal",
      type="double",
      bounds=dict(min=0, max=10),
      prior=dict(name="normal", mean=5, scale=scale),
    )
    with pytest.raises(ValueError):
      self.conn.experiments().create(
        parameters=[parameter_normal],
        metrics=[dict(name="y1", objective="maximize", strategy="optimize")],
      )

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  @pytest.mark.parametrize("shape_a, shape_b", [(1, -1), (-1, 1), (-1, -1), (0, 5), (5, 0), (0, 0)])
  def test_create_with_incorrect_beta_prior(self, shape_a, shape_b):
    parameter_beta = dict(
      name="parameter_beta",
      type="double",
      bounds=dict(min=0, max=1),
      prior=dict(name="beta", shape_a=-1, shape_b=10),
    )
    with pytest.raises(ValueError):
      self.conn.experiments().create(
        parameters=[parameter_beta],
        metrics=[dict(name="y1", objective="maximize", strategy="optimize")],
      )

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  @pytest.mark.parametrize("bounds", [dict(min=-20, max=-10), dict(min=-10, max=1), dict(min=0, max=10)])
  def test_log_transform_on_negative_bounds(self, bounds):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parameters"] = [dict(name="d", type="double", bounds=bounds, transformation="log")]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  @pytest.mark.parametrize("parameter", [PARAMETER_CATEGORICAL, PARAMETER_INT, PARAMETER_INT])
  def test_log_transform_on_incorrect_parameter_type(self, parameter):
    experiment_meta = self.get_experiment_feature("default")
    parameter["transformation"] = "log"
    experiment_meta["parameters"] = [parameter]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)


class TestExperimentConditionals(UnitTestsEndpoint):
  @pytest.mark.parametrize("feature", ["conditionals", "multiconditional"])
  def test_create_with_conditionals(self, feature):
    experiment_meta = self.get_experiment_feature(feature)
    e = self.conn.experiments().create(**experiment_meta)
    assert e.conditionals is not None

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_create_parameters_with_conditions_but_no_conditionals(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    for parameter in experiment_meta["parameters"]:
      parameter.pop("conditions", None)
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_create_conditionals_but_no_parameters_with_conditions(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    experiment_meta.pop("conditionals", None)
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_create_conditionals_parameter_condition_cannot_be_met(self):
    experiment_meta = self.get_experiment_feature("multiconditional")
    del experiment_meta["conditionals"][0]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

    experiment_meta = self.get_experiment_feature("multiconditional")
    experiment_meta["parameters"][3]["conditions"] = dict(z=["not_a_real_condition_in_meta"])
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  def test_no_conditionals_with_multisolution(self):
    experiment_meta = self.get_experiment_feature("conditionals")
    experiment_meta["num_solutions"] = 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  def test_no_conditionals_with_search(self):
    experiment_meta = self.get_experiment_feature("search")
    experiment_meta["num_solutions"] = 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)


class TestExperimentMultitask(UnitTestsEndpoint):
  def test_create_with_multitask(self):
    experiment_meta = self.get_experiment_feature("multitask")
    e = self.conn.experiments().create(**experiment_meta)
    assert e.tasks is not None

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  @pytest.mark.parametrize(
    "tasks",
    [
      [dict(name="one_task", cost=0.1)],
      [dict(name="zero_task", cost=0.0), dict(name="normal_task", cost=1.0)],
      [dict(name="negative_task", cost=-0.2), dict(name="normal_task", cost=1.0)],
      [dict(name="normal_task", cost=1.0), dict(name="too_expensive_task", cost=2.0)],
    ],
  )
  def test_create_with_bad_tasks(self, tasks):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta["tasks"] = tasks
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)


class TestExperimentMetrics(UnitTestsEndpoint):
  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_no_metrics(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["metrics"]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_empty_metrics(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = []
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_duplicate_metrics(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [dict(name="duplicated_metric", objective="maximize", strategy="optimize")] * 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.parametrize(
    "metrics",
    [
      [dict(name="metric", objective="maximize")],
      [dict(name="metric", objective="maximize", strategy="optimize")],
    ],
  )
  def test_single_metric_optimization(self, metrics):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = metrics
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].name == "metric"
    assert e.metrics[0].objective == "maximize"
    assert e.metrics[0].strategy == "optimize"

  @pytest.mark.parametrize(
    "metrics",
    [
      [dict(name="y1", objective="maximize"), dict(name="y2", objective="maximize")],
      [
        dict(name="y1", objective="maximize", strategy="optimize"),
        dict(name="y2", objective="maximize", strategy="optimize"),
      ],
    ],
  )
  def test_multi_metric_optimization(self, metrics):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = metrics
    e = self.conn.experiments().create(**experiment_meta)
    for metric in e.metrics:
      assert metric.objective == "maximize"
      assert metric.strategy == "optimize"

  def test_single_metric_constraint(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [dict(name="metric", objective="maximize", strategy="constraint", threshold=0.5)]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].name == "metric"
    assert e.metrics[0].objective == "maximize"
    assert e.metrics[0].strategy == "constraint"
    assert e.metrics[0].threshold == 0.5

  def test_search(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [
      dict(name="y1", objective="maximize", strategy="constraint", threshold=0.5),
      dict(name="y2", objective="maximize", strategy="constraint", threshold=0.5),
    ]
    e = self.conn.experiments().create(**experiment_meta)
    for metric in e.metrics:
      assert metric.objective == "maximize"
      assert metric.strategy == "constraint"
      assert metric.threshold == 0.5

  @pytest.mark.xfail  # Not being handled, need to throw error if three optimized metrics
  def test_too_many_optimized_metrics(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [
      dict(name="y1", objective="maximize", strategy="optimize"),
      dict(name="y2", objective="maximize", strategy="optimize"),
      dict(name="y3", objective="maximize", strategy="optimize"),
    ]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, wait for Gustavo's merge
  @pytest.mark.parametrize(
    "metrics",
    [
      [dict(name="metric")],
      [dict(name="metric", objective="invalid objective")],
      [dict(name=None, objective="invalid objective")],
      [dict(name=None, objective="")],
      [dict(name="bandwidth", threshold=23.6)],
      [dict(threshold=100), dict(objective="maximize")],
      [dict(name="metric1"), dict(name="metric2", objective="invalid objective")],
    ],
  )
  def test_invalid_metrics(self, metrics):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = metrics
    with pytest.raises(ValueError):
      self.conn.experiments().create(**experiment_meta)

  def test_experiment_create_multimetric_different_objectives(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [dict(name="cost", objective="minimize"), dict(name="profit", objective="maximize")]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.id is not None
    assert len(e.metrics) == 2
    assert e.metrics[0].name == "cost"
    assert e.metrics[0].objective == "minimize"
    assert e.metrics[1].name == "profit"
    assert e.metrics[1].objective == "maximize"

  def test_multimetric_no_thresholds(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [
      dict(
        name="metric_1",
        objective="maximize",
      ),
      dict(name="metric_2"),
    ]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold is None
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold is None

  @pytest.mark.parametrize("threshold_1", [None, 0.0, -0.0003])
  @pytest.mark.parametrize("threshold_2", [None, 0.0, 99.19])
  def test_multimetric_thresholds_specified(self, threshold_1, threshold_2):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["metrics"] = [
      dict(name="metric_1", objective="maximize", strategy="optimize", threshold=threshold_1),
      dict(name="metric_2", objective="maximize", strategy="optimize", threshold=threshold_2),
    ]
    e = self.conn.experiments().create(**experiment_meta)
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold == threshold_1
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold == threshold_2
