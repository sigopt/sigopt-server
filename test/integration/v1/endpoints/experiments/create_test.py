# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from zigopt.experiment.constant import MAX_CONSTRAINT_METRICS, MAX_METRICS_ANY_STRATEGY, MetricStrategyNames
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH

from integration.base import RaisesApiException
from integration.v1.constants import (
  DEFAULT_EXPERIMENT_META,
  EXPERIMENT_META_CONDITIONALS,
  EXPERIMENT_META_MULTISOLUTION,
  CategoricalParameterMetaType,
)
from integration.v1.experiments_test_base import ExperimentsTestBase
from libsigopt.aux.constant import ParameterTransformationNames


class TestCreateExperiments(ExperimentsTestBase):
  # pylint: disable=too-many-public-methods
  def test_experiment_create(self, connection, client_id, any_meta):
    e = connection.clients(client_id).experiments().create(**any_meta)
    assert e.id is not None

  def test_experiment_create_no_metric(self, connection, client_id):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    del meta["metrics"]
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id is not None
    assert len(e.metrics) == 1
    assert e.metrics[0].name is None
    assert e.metrics[0].objective == "maximize"

  def test_experiment_create_no_name(self, connection, client_id, any_meta):
    meta = copy.deepcopy(any_meta)
    del meta["name"]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_experiment_create_no_budget(self, connection, client_id):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    del meta["observation_budget"]
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id is not None
    assert e.observation_budget is None

  def test_experiment_create_no_parameters(self, connection, client_id, any_meta):
    meta = copy.deepcopy(any_meta)
    del meta["parameters"]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_experiment_create_empty_parameters(self, connection, client_id, any_meta):
    meta = copy.deepcopy(any_meta)
    meta["parameters"] = []
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_experiment_create_extra_parameters(self, connection, client_id, any_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(foo="bar", **any_meta)

  def test_experiment_create_bad_parameters(self, connection, client_id, any_meta):
    meta = copy.deepcopy(any_meta)
    meta["parameters"][0]["type"] = "invalid_type"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  # NOTE: Current bug. Nested keys should be errors here. We should fix this
  # but we should make sure it won't impact any existing customers
  @pytest.mark.xfail
  def test_experiment_create_nested_extra_parameters(self, connection, client_id, any_meta):
    meta = copy.deepcopy(any_meta)
    meta["parameters"][0]["foo"] = "bar"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_categorical_values_array_of_strings(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        name="default experiment",
        parameters=[
          dict(name="c", type="categorical", categorical_values=["d", "e"]),
        ],
      )
    )
    (p,) = e.parameters
    (cat1, cat2) = sorted(p.categorical_values, key=lambda c: c.enum_index)
    assert cat1.enum_index == 1
    assert cat1.name == "d"
    assert cat2.enum_index == 2
    assert cat2.name == "e"

  @pytest.mark.parametrize(
    "metrics_json, error",
    [
      (
        [],
        "The `metrics` list must contain a metric",
      ),
      (
        [dict(), dict()],
        "Multimetric experiments do not support unnamed metrics",
      ),
      (
        [dict(name="metric"), dict(name="metric")],
        "Duplicate metric name: metric",
      ),
    ],
  )
  def test_experiment_invalid_metrics(self, connection, client_id, metrics_json, error):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as exception_info:
      connection.create_any_experiment(observation_budget=60, client_id=client_id, metrics=metrics_json)
    assert error in str(exception_info)

  @pytest.mark.parametrize(
    "metric_json",
    [
      dict(threshold=100),
      dict(objective="maximize"),
    ],
  )
  def test_experiment_invalid_metric(self, connection, client_id, metric_json):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(client_id=client_id, metric=metric_json)

  def test_experiment_unnamed_and_specified_objective_metric(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id, metrics=[dict(objective="minimize")])
    assert e.metrics[0].objective == "minimize"

  @pytest.mark.parametrize(
    "metrics_json",
    [
      [dict(name="metric", objective="invalid objective")],
      [dict(name=None, objective="invalid objective")],
      [dict(name=None, objective="")],
      [dict(name="metric1"), dict(name="metric2", objective="invalid objective")],
    ],
  )
  def test_experiment_invalid_objective(self, connection, client_id, metrics_json):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(client_id=client_id, metrics=metrics_json)

  def test_experiment_create_multimetric_different_objectives(
    self,
    connection,
    client_id,
  ):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["metrics"] = [dict(name="cost", objective="minimize"), dict(name="profit", objective="maximize")]
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id is not None
    assert len(e.metrics) == 2
    assert e.metrics[0].name == "cost"
    assert e.metrics[0].objective == "minimize"
    assert e.metrics[1].name == "profit"
    assert e.metrics[1].objective == "maximize"

  @pytest.mark.parametrize(
    "metrics_json",
    [
      [dict(name="cost")],
      [dict(name="accuracy", objective="minimize")],
    ],
  )
  def test_can_create_single_metric_different_objectives(
    self,
    connection,
    client_id,
    metrics_json,
  ):
    connection.create_any_experiment(client_id=client_id, metrics=metrics_json)

  @pytest.mark.parametrize(
    "metrics_json",
    [
      [dict()],
      [dict(name=None)],
      [dict(name="metric"), dict()],
      [dict(name="name", objective=None)],
    ],
  )
  @pytest.mark.xfail(reason="The web interface may give us unexpected data")
  def test_experiment_invalid_metrics_xfail(self, connection, client_id, metrics_json):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(client_id=client_id, metrics=metrics_json)

  def test_single_metric_threshold_fails(self, connection, client_id):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        name="test",
        client_id=client_id,
        observation_budget=60,
        metrics=[
          dict(name="bandwidth", threshold=23.6),
        ],
      )

  @pytest.mark.parametrize("threshold_1", [None, 0.0, -0.0003])
  @pytest.mark.parametrize("threshold_2", [None, 0.0, 99.19])
  def test_multimetric_threshold_both_specified(
    self,
    connection,
    client_id,
    threshold_1,
    threshold_2,
  ):
    e = connection.create_any_experiment(
      client_id=client_id,
      observation_budget=60,
      metrics=[
        dict(name="metric_1", threshold=threshold_1),
        dict(name="metric_2", threshold=threshold_2),
      ],
    )
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold == threshold_1
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold == threshold_2

  @pytest.mark.parametrize("threshold", [None, 0.0, -500.403])
  def test_multimetric_threshold_one_specified(
    self,
    connection,
    client_id,
    threshold,
  ):
    e = connection.create_any_experiment(
      client_id=client_id,
      observation_budget=60,
      metrics=[
        dict(name="metric_1", threshold=threshold),
        dict(name="metric_2"),
      ],
    )
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold == threshold
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold is None
    e = connection.create_any_experiment(
      client_id=client_id,
      observation_budget=60,
      metrics=[
        dict(name="metric_1"),
        dict(name="metric_2", threshold=threshold),
      ],
    )
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold is None
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold == threshold

  def test_multimetric_no_thresholds(
    self,
    connection,
    client_id,
  ):
    e = connection.create_any_experiment(
      client_id=client_id,
      observation_budget=60,
      metrics=[
        dict(name="metric_1"),
        dict(name="metric_2"),
      ],
    )
    assert e.metrics[0].name == "metric_1"
    assert e.metrics[0].threshold is None
    assert e.metrics[1].name == "metric_2"
    assert e.metrics[1].threshold is None

  def test_default_parallel_bandwidth(self, connection, client_id, any_meta, services):
    e = connection.clients(client_id).experiments().create(**any_meta)
    assert e.parallel_bandwidth is None
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.parallel_bandwidth == 1

  @pytest.mark.parametrize("parallel_bandwidth", list(range(2, 5)))
  def test_experiment_create_with_parallel_bandwidth(self, connection, client_id, parallel_bandwidth):
    e = connection.create_any_experiment(
      client_id=client_id,
      parallel_bandwidth=parallel_bandwidth,
    )
    assert e.parallel_bandwidth == parallel_bandwidth

  @pytest.mark.parametrize("parallel_bandwidth", [0, -1])
  def test_experiment_create_invalid_parallel_bandwidth(self, connection, client_id, parallel_bandwidth):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        parallel_bandwidth=parallel_bandwidth,
      )

  def test_max_categorical_breadth_does_not_count_parameters(self, connection, client_id):
    experiment = connection.create_any_experiment(
      client_id=client_id,
      parameters=[dict(name=f"p{i}", type="double", bounds=dict(min=0, max=1)) for i in range(11)],
    )
    assert len(experiment.parameters) > 2

  def test_metrics_list_strings(self, connection, client_id):
    e = connection.create_any_experiment(
      client_id=client_id,
      metrics=["metric1"],
      observation_budget=60,
    )
    assert len(e.metrics) == 1

  def test_metrics_list_too_many_metrics(self, connection, client_id):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        metrics=["metric1", "metric2", "metric3"],
        observation_budget=60,
      )

  def test_empty_string_metric(self, connection, client_id):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        metrics=[""],
        observation_budget=60,
      )

  def test_create_with_project(self, connection, client_id, project):
    experiment = connection.create_any_experiment(
      client_id=client_id,
      project=project.id,
    )
    assert experiment.project == project.id
    fetched_experiment = connection.experiments(experiment.id).fetch()
    assert fetched_experiment.project == project.id

  @pytest.mark.parametrize(
    "project_reference_id",
    [
      "",
      "not-a-valid-project",
      "X" * (MAX_PROJECT_ID_LENGTH + 1),
    ],
  )
  def test_create_with_invalid_project(self, project_reference_id, connection, client_id):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        project=project_reference_id,
      )

  @pytest.mark.parametrize(
    "prior",
    [
      dict(name="normal", mean=0.0, scale=1.0),
      dict(name="beta", shape_a=1.5, shape_b=2.5),
    ],
  )
  def test_create_with_parameter_priors(
    self,
    connection,
    client_id,
    prior,
  ):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    assert meta["parameters"][1]["type"] == "double"
    meta["parameters"][1]["prior"] = prior
    experiment = connection.clients(client_id).experiments().create(**meta)
    # @TODO: can update to dot-notation when prior exists in sigopt-python
    parameter_json = experiment.parameters[1].to_json()
    assert "prior" in parameter_json
    created_prior = parameter_json["prior"]
    for key, value in prior.items():
      assert created_prior[key] == value

  def test_create_with_multitask_and_conditionals(
    self,
    connection,
    client_id,
  ):
    meta = copy.deepcopy(EXPERIMENT_META_CONDITIONALS)
    meta["tasks"] = [
      dict(name="cheap", cost=0.1),
      dict(name="expensive", cost=1.0),
    ]
    experiment = connection.clients(client_id).experiments().create(**meta)
    assert experiment.conditionals is not None
    assert experiment.tasks is not None


class TestCreateExperimentsWithMetricStrategy(ExperimentsTestBase):
  # pylint: disable=too-many-public-methods
  def test_strategy_optimize(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[dict(name="metric", strategy=MetricStrategyNames.OPTIMIZE)],
    )
    assert len(e.metrics) == 1
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is False
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_single_optimized_metric_with_stored_metric(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="metric1"),
        dict(name="metric2", strategy=MetricStrategyNames.STORE),
      ]
    )
    assert len(e.metrics) == 2
    assert e.metrics[0].name == "metric1"
    assert e.metrics[1].name == "metric2"
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_single_optimized_metric_with_stored_metric_alphabetically_first(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="optimized-metric"),
        dict(name="a-stored-metric", strategy=MetricStrategyNames.STORE),
      ]
    )
    assert len(e.metrics) == 2
    assert e.metrics[0].name == "a-stored-metric"
    assert e.metrics[1].name == "optimized-metric"
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_multiple_optimized_metric_with_stored_metric(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="metric1"),
        dict(name="metric2"),
        dict(name="metric3", strategy=MetricStrategyNames.STORE),
      ],
      observation_budget=10,
    )
    assert len(e.metrics) == 3
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is True

  def test_conditionals_with_stored_metrics(self, connection, services):
    meta = copy.deepcopy(EXPERIMENT_META_CONDITIONALS)
    metrics = meta.get("metrics")
    if metrics is None:
      metrics = []
    meta["metrics"] = [*metrics, dict(name="stored-metric", strategy="store")]
    e = connection.create_any_experiment(**meta)
    assert e.conditionals is not None
    assert len(e.metrics) == 2
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_multisolution_with_stored_metrics(self, connection, services):
    meta = copy.deepcopy(EXPERIMENT_META_MULTISOLUTION)
    meta["metrics"] = [
      dict(name="metric"),
      dict(name="stored-metric", strategy="store"),
    ]

    e = connection.create_any_experiment(**meta)
    assert e.num_solutions == 2
    assert len(e.metrics) == 2
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_optimized_metric_thresholds_with_stored_metrics(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="optimized-1", threshold=1.0),
        dict(name="optimized-2", threshold=2.0),
        dict(name="stored-1", strategy=MetricStrategyNames.STORE),
      ],
      observation_budget=10,
    )

    assert len(e.metrics) == 3
    assert e.metrics[0].threshold == 1.0
    assert e.metrics[1].threshold == 2.0
    assert e.metrics[2].threshold is None
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is True

  def test_single_constraint_metric(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="constraint-1", strategy=MetricStrategyNames.CONSTRAINT, threshold=2.0),
      ],
      observation_budget=10,
    )

    assert len(e.metrics) == 1
    assert e.metrics[0].threshold == 2.0
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is False
    assert zigopt_experiment.is_search is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_constraint_metrics(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="constraint-1", strategy=MetricStrategyNames.CONSTRAINT, threshold=1.0),
        dict(name="constraint-2", strategy=MetricStrategyNames.CONSTRAINT, threshold=2.0),
      ],
      observation_budget=10,
    )

    assert len(e.metrics) == 2
    assert e.metrics[0].threshold == 1.0
    assert e.metrics[1].threshold == 2.0
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.is_search is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_constraints_with_stored_metrics(self, connection, services):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="constraint-1", strategy=MetricStrategyNames.CONSTRAINT, threshold=1.0),
        dict(name="constraint-2", strategy=MetricStrategyNames.CONSTRAINT, threshold=2.0),
        dict(name="stored-1", strategy=MetricStrategyNames.STORE),
      ],
      observation_budget=10,
    )

    assert len(e.metrics) == 3
    assert e.metrics[0].threshold == 1.0
    assert e.metrics[1].threshold == 2.0
    assert e.metrics[2].threshold is None
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.has_multiple_metrics is True
    assert zigopt_experiment.is_search is True
    assert zigopt_experiment.requires_pareto_frontier_optimization is False

  def test_no_optimized_metrics_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[dict(name="metric1", strategy=MetricStrategyNames.STORE)],
      )

  def test_too_many_metrics_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=(
          [dict(name="optimized-metric1")]
          + [dict(name=f"stored-{i}", strategy=MetricStrategyNames.STORE) for i in range(MAX_METRICS_ANY_STRATEGY)]
        )
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=(
          [
            dict(name="optimized-metric1"),
            dict(name="optimized-metric2"),
          ]
          + [dict(name=f"stored-{i}", strategy=MetricStrategyNames.STORE) for i in range(MAX_METRICS_ANY_STRATEGY - 1)]
        )
      )

  def test_non_unique_metric_names_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="metric"),
          dict(name="metric", strategy=MetricStrategyNames.STORE),
        ]
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="metric"),
          dict(name="stored_metric", strategy=MetricStrategyNames.STORE),
          dict(name="stored_metric", strategy=MetricStrategyNames.STORE),
        ]
      )

  def test_threshold_on_stored_metric_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimized-1", threshold=1.0),
          dict(name="optimized-2", threshold=2.0),
          dict(name="stored-1", threshold=3.0, strategy=MetricStrategyNames.STORE),
        ],
        observation_budget=10,
      )

  def test_too_many_constraint_metrics_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=(
          [dict(name="optimized-metric1")]
          + [
            dict(name=f"constraint-{i}", strategy=MetricStrategyNames.CONSTRAINT)
            for i in range(MAX_CONSTRAINT_METRICS + 1)
          ]
        )
      )

  def test_no_threshold_on_constraint_metric_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimized-1"),
          dict(name="constraint-1", strategy=MetricStrategyNames.CONSTRAINT),
        ],
        observation_budget=10,
      )

  def test_invalid_threshold_on_constraint_metric_raises_error(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimized-1"),
          dict(name="constraint-1", strategy=MetricStrategyNames.CONSTRAINT, threshold=None),
        ],
        observation_budget=10,
      )

  def test_threshold_with_one_optimized_one_stored_metrics_raises_error(
    self,
    connection,
  ):
    # without threshold on stored metric, since we know that fails
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimized-1", threshold=1.0),
          dict(name="stored-1", strategy=MetricStrategyNames.STORE),
        ],
        observation_budget=10,
      )

    # with threshold on stored metric to make sure no weird counting of thresholds accidentally passes
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimized-1", threshold=1.0),
          dict(name="stored-1", threshold=2.0, strategy=MetricStrategyNames.STORE),
        ],
        observation_budget=10,
      )

  def test_log_transform_params(self, connection, services):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [dict(name="a", type="double", bounds=dict(min=0.1, max=10), transformation="log")]
    e = connection.create_any_experiment(**meta)
    assert e.parameters[0].to_json()["transformation"] == ParameterTransformationNames.LOG
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    zigopt_parameter = zigopt_experiment.all_parameters_sorted[0]
    assert zigopt_parameter.has_log_transformation

  @pytest.mark.parametrize(
    "bounds",
    [
      dict(min=0, max=10),
      dict(min=-1, max=1),
      dict(min=-10, max=0),
      dict(min=-10, max=-1),
    ],
  )
  def test_log_transform_errors_on_non_positive_bounds(self, connection, bounds):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [dict(name="a", type="double", bounds=bounds, transformation="log")]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(**meta)

  def test_log_transform_errors_on_non_double(self, connection):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)

    meta["parameters"] = [dict(name="a", type="int", bounds=dict(min=1, max=10), transformation="log")]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(**meta)

    meta["parameters"] = [
      CategoricalParameterMetaType(  # type: ignore
        name="cat",
        type="categorical",
        categorical_values=[dict(name="d"), dict(name="e")],
        transformation="log",
      ),
    ]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(**meta)

  def test_log_transform_errors_on_parameter_priors(self, connection):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [
      dict(
        name="a",
        type="double",
        bounds=dict(min=1, max=10),
        transformation="log",
        prior=dict(name="normal", mean=0.0, scale=1.0),
      )
    ]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(**meta)

  def test_log_transform_errors_only_on_parameters_also_with_constraints(self, connection):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [
      dict(name="a", type="double", bounds=dict(min=1, max=10)),
      dict(name="b", type="double", bounds=dict(min=1, max=10)),
      dict(name="c", type="double", bounds=dict(min=1, max=10), transformation="log"),
    ]
    meta["linear_constraints"] = [
      dict(
        type="greater_than",
        terms=[
          dict(name="a", weight=1),
          dict(name="b", weight=1),
        ],
        threshold=10,
      ),
    ]

    e = connection.create_any_experiment(**meta)
    assert e.id

    linear_constraints = meta["linear_constraints"]
    assert linear_constraints
    linear_constraints[0]["terms"].append(dict(name="c", weight=1))
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(**meta)

  def test_log_transform_with_conditionals(self, connection):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [
      dict(
        name="a",
        type="double",
        bounds=dict(min=1, max=10),
        conditions=dict(x=["foo", "bar"]),
        transformation="log",
      ),
      dict(
        name="b",
        type="double",
        bounds=dict(min=1, max=10),
        conditions=dict(x=["foo", "baz"]),
        transformation="log",
      ),
    ]
    meta["conditionals"] = [
      dict(name="x", values=["foo", "bar", "baz"]),
    ]
    e = connection.create_any_experiment(**meta)
    assert e.id

  def test_create_runs_only(self, connection, project):
    experiment = (
      connection.clients(connection.client_id)
      .experiments()
      .create(
        name="test create runs only",
        parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
        metrics=[{"name": "m1"}],
        runs_only=True,
        project=project.id,
      )
    )
    assert experiment.to_json()["runs_only"] is True
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.experiments(experiment.id).suggestions().create()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.experiments(experiment.id).observations().create()

  def test_create_runs_only_with_budget(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .experiments()
        .create(
          name="test create runs only",
          parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
          metrics=[{"name": "m1"}],
          runs_only=True,
          observation_budget=123,
          project=project.id,
        )
      )

    experiment = (
      connection.clients(connection.client_id)
      .experiments()
      .create(
        name="test create runs only",
        parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
        metrics=[{"name": "m1"}],
        runs_only=True,
        budget=123,
        project=project.id,
      )
    )
    assert experiment.to_json()["budget"] == 123

  def test_budget_invalid_without_runs_only(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .experiments()
        .create(
          name="test create runs only",
          parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
          metrics=[{"name": "m1"}],
          runs_only=False,
          budget=123,
          project=project.id,
        )
      )

  def test_create_progress_runs_only(self, connection, project):
    experiment = (
      connection.clients(connection.client_id)
      .experiments()
      .create(
        name="test create runs only",
        parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
        metrics=[{"name": "m1"}],
        runs_only=True,
        project=project.id,
      )
    )
    assert experiment.to_json()["runs_only"] is True
    progress_data = experiment.progress.to_json()
    assert progress_data["object"] == "progress"
    assert progress_data["active_run_count"] == 0
    assert progress_data["finished_run_count"] == 0
    assert progress_data["total_run_count"] == 0
    assert progress_data["remaining_budget"] is None

  def test_create_runs_only_no_project(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .experiments()
        .create(
          name="test create runs only",
          parameters=[{"name": "p1", "type": "double", "bounds": {"min": 0, "max": 1}}],
          metrics=[{"name": "m1"}],
          runs_only=True,
        )
      )
