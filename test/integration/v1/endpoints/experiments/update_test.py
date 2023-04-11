# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_epoch as get_unix_epoch
from zigopt.experiment.constant import MetricStrategyNames
from zigopt.experiment.model import Experiment
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentsTestBase
from libsigopt.aux.constant import ParameterTransformationNames


unix_epoch_timestamp = 0
unix_epoch = get_unix_epoch()


class TestUpdateExperiments(ExperimentsTestBase):
  @pytest.fixture(autouse=True)
  def setup_assert_experiment(self, connection):
    self.connection = connection

  def assert_experiment_updated(self, e, checker):
    assert checker(e) is True
    assert checker(self.connection.experiments(e.id).fetch())

  def test_name_update(self, connection, client_id, any_meta):
    e = connection.clients(client_id).experiments().create(**any_meta)
    e = connection.experiments(e.id).update(name="updated name")
    self.assert_experiment_updated(e, lambda e: e.name == "updated name")

  def test_parameter_update(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id)
    assert len(e.parameters) != 1
    p = find(e.parameters, lambda p: p.type == "int")
    e = connection.experiments(e.id).update(
      parameters=[dict(name=p.name, type=p.type, bounds=dict(min=p.bounds.min - 1, max=p.bounds.max + 1))]
    )
    self.assert_experiment_updated(e, lambda e: len(e.parameters) == 1)

  def test_experiment_update_nothing(self, connection, client_id, any_meta):
    original = connection.clients(client_id).experiments().create(**any_meta)
    e = connection.experiments(original.id).update()
    self.assert_experiment_updated(e, lambda e: omit(e.to_json(), "updated") == omit(original.to_json(), "updated"))

  def test_experiment_update_state(self, connection):
    e = connection.create_any_experiment()
    e = connection.experiments(e.id).update(state="deleted")
    self.assert_experiment_updated(e, lambda e: e.state == "deleted")

  def test_experiment_update_budget(self, connection):
    with connection.create_any_experiment() as e:
      e = connection.experiments(e.id).update(observation_budget=20)
      self.assert_experiment_updated(e, lambda e: e.observation_budget == 20)

  def test_experiment_update_type(self, connection):
    # Cannot include type key in json dict
    with connection.create_any_experiment() as e:
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(type="offline")

  def test_bad_parameters_update(self, connection, any_meta):
    # NOTE: cannot update parameters for an experiment with constraints
    e = connection.create_experiment({k: v for k, v in any_meta.items() if k != "linear_constraints"})

    # Parameters can't be None
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=None)

    # No duplicate parameter names
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        **{
          "parameters": [
            {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
            {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
            {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
            {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
          ],
        }
      )

    # New parameters need default_value
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        **{
          "parameters": [
            {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
            {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
            {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
            {"name": "d", "type": "double", "bounds": {"min": -50, "max": 0}},
          ],
        }
      )

    # Can't delete all parameters
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        **{
          "parameters": [],
        }
      )

    # Can't update wrong_key
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(**{"wrong_key": "nothing"})

    # Can't change type of a parameter
    parameters = e.parameters
    find(parameters, lambda p: p.type == "int").type = "double"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=parameters)

  def test_resurrected_params_need_default_value(self, connection):
    update_keys = ["name", "type", "bounds", "categorical_values", "default_value"]

    e = connection.create_any_experiment()

    connection.experiments(e.id).update(
      parameters=[pick(p.to_json(), *update_keys) for p in e.parameters if p.type != "double"]
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[pick(p.to_json(), *update_keys) for p in e.parameters])
    for parameter in e.parameters:
      if parameter.type == "double":
        parameter.default_value = 1
    parameters = e.parameters
    e = connection.experiments(e.id).update(parameters=[pick(p.to_json(), *update_keys) for p in parameters])
    self.assert_experiment_updated(e, lambda e: e.parameters == parameters)

  def test_update_double_parameter(self, connection):
    e = connection.create_any_experiment()
    connection.experiments(e.id).update(
      parameters=[
        {"name": "a", "type": "double", "bounds": {"min": 0, "max": 1}, "default_value": 0.5},
      ]
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[{"name": "a", "default_value": 1.5}])

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[{"name": "a", "default_value": -0.5}])

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "a", "type": "double", "bounds": {"min": 0.8, "max": 1}, "default_value": 0.5},
        ]
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "a", "type": "double", "bounds": {"min": 0.8, "max": 1}},
        ]
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "a", "type": "double", "bounds": {"min": 0.0, "max": 0.2}, "default_value": 0.5},
        ]
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "a", "type": "double", "bounds": {"min": 0.0, "max": 0.2}},
        ]
      )

    connection.experiments(e.id).update(
      parameters=[
        {"name": "a", "type": "double", "bounds": {"min": -10, "max": -1}, "default_value": -5},
      ]
    )
    connection.experiments(e.id).update(
      parameters=[
        {"name": "a", "type": "double", "bounds": {"min": 1, "max": 10}, "default_value": 5},
      ]
    )

  def test_update_categorical_parameter(self, connection):
    e = connection.create_any_experiment()
    connection.experiments(e.id).update(
      parameters=[
        {
          "name": "c",
          "type": "categorical",
          "categorical_values": [{"name": "1"}, {"name": "2"}],
          "default_value": "2",
        },
      ]
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[{"name": "c", "default_value": "f"}])

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "c", "type": "categorical", "categorical_values": [{"name": "1"}], "default_value": "2"},
        ]
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          {"name": "c", "type": "categorical", "categorical_values": [{"name": "1"}]},
        ]
      )

    connection.experiments(e.id).update(
      parameters=[
        {
          "name": "c",
          "type": "categorical",
          "categorical_values": [{"name": "3"}, {"name": "4"}],
          "default_value": "4",
        },
      ]
    )

  def test_update_categorical_values_array_of_strings(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        name="default experiment",
        parameters=[
          dict(name="c", type="categorical", categorical_values=["d", "f"]),
        ],
      )
    )

    e = connection.experiments(e.id).update(
      parameters=[
        dict(name="c", categorical_values=["d", "e"]),
      ]
    )
    (p,) = e.parameters
    (cat1, cat2) = sorted(p.categorical_values, key=lambda c: c.enum_index)
    assert cat1.enum_index == 1
    assert cat1.name == "d"
    assert cat2.enum_index == 3
    assert cat2.name == "e"

  def test_too_few_categorical_values(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        name="default experiment",
        parameters=[
          dict(name="c", type="categorical", categorical_values=["d", "f"]),
        ],
      )
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          dict(name="c", categorical_values=["d"]),
        ]
      )

  def test_experiment_update_parallel_bandwidth(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id)
    assert e.parallel_bandwidth is None
    e = connection.experiments(e.id).update(parallel_bandwidth=3)
    assert e.parallel_bandwidth == 3
    e = connection.experiments(e.id).update(parallel_bandwidth=None)
    assert e.parallel_bandwidth is None

  @pytest.mark.parametrize("metrics", [None, "string", 1, 0, {}])
  def test_update_metics_invalid_types555(self, connection, client_id, metrics):
    e = connection.create_any_experiment(metrics=[{"name": "cost"}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(metrics=metrics)

  def test_cant_update_metric_objective(self, connection, client_id):
    e = connection.create_any_experiment(metrics=[{"name": "cost"}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(metrics=[{"objective": "minimize"}])

  def test_can_update_unspecified_metric_objective(
    self,
    connection,
    client_id,
  ):
    e = connection.create_any_experiment(metrics=[{"name": "cost"}])
    e = connection.experiments(e.id).update(metrics=[{"objective": "maximize"}])
    e = connection.experiments(e.id).fetch()
    assert e.metrics[0].name == "cost"
    assert e.metrics[0].objective == "maximize"

  def test_can_update_metric_same_objective(self, connection, client_id):
    e = connection.create_any_experiment(metrics=[{"name": "cost", "objective": "maximize"}])
    e = connection.experiments(e.id).update(metrics=[{"objective": "maximize"}])
    e = connection.experiments(e.id).fetch()
    assert e.metrics[0].name == "cost"
    assert e.metrics[0].objective == "maximize"
    e = connection.create_any_experiment(metrics=[{"name": "cost", "objective": "minimize"}])
    e = connection.experiments(e.id).update(metrics=[{"objective": "minimize"}])
    e = connection.experiments(e.id).fetch()
    assert e.metrics[0].name == "cost"
    assert e.metrics[0].objective == "minimize"

  def test_experiment_update_metrics_multiple_optimized(self, connection, client_id):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "return"},
        {"name": "safety", "threshold": 0.2},
      ],
    )
    e = connection.experiments(e.id).update(
      metrics=[
        {"name": "return", "threshold": 100.0},
        {"name": "safety", "threshold": None},
      ]
    )
    e = connection.experiments(e.id).fetch()
    self.assert_experiment_updated(
      e,
      lambda exp: all(
        [
          exp.metrics[0].name == "return",
          exp.metrics[0].threshold == 100.0,
          exp.metrics[1].name == "safety",
          exp.metrics[1].threshold is None,
        ]
      ),
    )

  def test_experiment_update_metrics_multiple_optimized_swap_order(
    self,
    connection,
    client_id,
  ):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "risk", "objective": "maximize"},
        {"name": "return", "objective": "minimize"},
      ],
    )
    e = connection.experiments(e.id).update(
      metrics=[
        {"name": "return", "objective": "minimize", "threshold": 2.0},
        {"name": "risk", "objective": "maximize", "threshold": 3.0},
      ]
    )
    e = connection.experiments(e.id).fetch()
    assert e.metrics[0].name == "return"
    assert e.metrics[0].objective == "minimize"
    assert e.metrics[0].threshold == 2.0
    assert e.metrics[1].name == "risk"
    assert e.metrics[1].objective == "maximize"
    assert e.metrics[1].threshold == 3.0
    e = connection.experiments(e.id).update(
      metrics=[
        {"name": "risk", "objective": "maximize", "threshold": 5.0},
        {"name": "return", "objective": "minimize", "threshold": 4.0},
      ]
    )
    e = connection.experiments(e.id).fetch()
    assert e.metrics[0].name == "return"
    assert e.metrics[0].objective == "minimize"
    assert e.metrics[0].threshold == 4.0
    assert e.metrics[1].name == "risk"
    assert e.metrics[1].objective == "maximize"
    assert e.metrics[1].threshold == 5.0

  def test_experiment_unchanged_update_metrics_multiple_optimized(
    self,
    connection,
    client_id,
  ):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "return"},
        {"name": "safety", "threshold": 0.2},
      ],
    )
    e = connection.experiments(e.id).update(
      metrics=[
        {"name": "return"},
        {"name": "safety"},
      ]
    )
    e = connection.experiments(e.id).fetch()
    self.assert_experiment_updated(
      e,
      lambda exp: all(
        [
          exp.metrics[0].name == "return",
          exp.metrics[0].threshold is None,
          exp.metrics[1].name == "safety",
          exp.metrics[1].threshold == 0.2,
        ]
      ),
    )

  def test_experiment_invalid_update_metrics_multiple_optimized(
    self,
    connection,
    client_id,
  ):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "return"},
        {"name": "safety", "threshold": 0.2},
      ],
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        metrics=[{"name": "return"}],
      )

  @pytest.mark.parametrize("objective", ["minimize", "maximize"])
  @pytest.mark.parametrize("threshold", ["100.0", True, "abc"])
  def test_experiment_update_metrics_invalid_threshold_input(
    self,
    connection,
    client_id,
    threshold,
    objective,
  ):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "return"},
        {"name": "safety", "objective": objective, "threshold": 0.2},
      ],
    )
    connection.experiments(e.id).update(
      metrics=[
        {"name": "return"},
        {"name": "safety", "objective": objective},
      ]
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        metrics=[
          {"name": "return", "threshold": threshold},
          {"name": "safety", "objective": objective},
        ]
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        metrics=[
          {"name": "return", "threshold": threshold, "objective": objective},
          {"name": "safety"},
        ]
      )

  @pytest.mark.parametrize("objective", [0, None, True, "min"])
  @pytest.mark.parametrize("threshold", [None, 0.0])
  def test_experiment_update_metrics_invalid_objective_input(
    self,
    connection,
    client_id,
    threshold,
    objective,
  ):
    e = connection.create_any_experiment(
      name="test_exp",
      observation_budget=100,
      metrics=[
        {"name": "return"},
        {"name": "safety", "objective": "minimize", "threshold": threshold},
      ],
    )
    connection.experiments(e.id).update(
      metrics=[
        {"name": "return", "threshold": threshold},
        {"name": "safety"},
      ]
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        metrics=[
          {"name": "return", "threshold": threshold},
          {"name": "safety", "objective": objective},
        ]
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        metrics=[
          {"name": "return"},
          {"name": "safety", "threshold": threshold, "objective": objective},
        ]
      )

  def test_experiment_update_project(self, connection, project):
    with connection.create_any_experiment() as e:
      for _ in range(2):
        updated_experiment = connection.experiments(e.id).update(project=project.id)
        self.assert_experiment_updated(
          updated_experiment,
          lambda e: e.project == project.id,
        )

  def test_experiment_clear_project(self, connection, project):
    with connection.create_any_experiment(project=project.id) as e:
      updated_experiment = connection.experiments(e.id).update(project=project.id)
      self.assert_experiment_updated(
        updated_experiment,
        lambda e: e.project == project.id,
      )
      for _ in range(2):
        updated_experiment = connection.experiments(e.id).update(project=None)
        self.assert_experiment_updated(
          updated_experiment,
          lambda e: e.project is None,
        )

  def test_experiment_update_bad_project(self, connection):
    with connection.create_any_experiment() as e:
      assert e.project is None
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(
          project=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        )
      updated_e = connection.experiments(e.id).fetch()
      assert updated_e.project is None

  def test_experiment_update_changes_time(self, services, connection):
    with connection.create_any_experiment() as e:
      services.database_service.update(
        services.database_service.query(Experiment).filter(Experiment.id == int(e.id)),
        {Experiment.date_updated: unix_epoch},
      )
      assert connection.experiments(e.id).fetch().updated == unix_epoch_timestamp
      updated_e = connection.experiments(e.id).update()
      assert updated_e.updated > unix_epoch_timestamp
      fetched_e = connection.experiments(e.id).fetch()
      assert fetched_e.updated > unix_epoch_timestamp
      assert updated_e.updated == fetched_e.updated

  def _compare_metric_lists(self, metric_list_1, metric_list_2):
    assert [m.to_json() for m in metric_list_1] == [m.to_json() for m in metric_list_2]

  def test_update_strategy_same_value(self, services, connection):
    metrics = [{"name": "metric1"}, {"name": "stored", "strategy": MetricStrategyNames.STORE}]
    with connection.create_any_experiment(metrics=metrics) as e:
      updated_e = connection.experiments(e.id).update(metrics=metrics)
      self._compare_metric_lists(updated_e.metrics, e.metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, updated_e.metrics)

  def test_update_strategy_change_raises(self, services, connection):
    metrics = [{"name": "metric1", "strategy": MetricStrategyNames.OPTIMIZE}]
    with connection.create_any_experiment(metrics=metrics) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["strategy"] = MetricStrategyNames.STORE
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

    metrics = [
      {"name": "optimized1"},
      {"name": "stored", "strategy": MetricStrategyNames.STORE},
    ]
    with connection.create_any_experiment(metrics=metrics) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[1]["strategy"] = MetricStrategyNames.CONSTRAINT
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

  def test_update_threshold_one_optimized_one_stored_raises(self, services, connection):
    metrics = [{"name": "optimized"}, {"name": "stored", "strategy": MetricStrategyNames.STORE}]
    with connection.create_any_experiment(metrics=metrics) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = 1.23
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

  def test_update_threshold_only_optimized(self, services, connection):
    metrics = [
      {"name": "optimized1"},
      {"name": "optimized2"},
      {"name": "stored", "strategy": MetricStrategyNames.STORE},
    ]
    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = 1.23
      new_metrics[1]["threshold"] = 4.56
      updated_e = connection.experiments(e.id).update(metrics=new_metrics)
      assert updated_e.metrics[0].threshold == 1.23
      assert updated_e.metrics[1].threshold == 4.56
      assert updated_e.metrics[2].threshold is None
      fetched_e = connection.experiments(e.id).fetch()
      assert fetched_e.metrics[0].threshold == 1.23
      assert fetched_e.metrics[1].threshold == 4.56
      assert fetched_e.metrics[2].threshold is None

  def test_update_threshold_on_stored_stays_none(self, services, connection):
    metrics = [
      {"name": "optimized1"},
      {"name": "optimized2"},
      {"name": "stored", "strategy": MetricStrategyNames.STORE},
    ]
    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = 1.23
      new_metrics[1]["threshold"] = 4.56
      new_metrics[2]["threshold"] = None
      updated_e = connection.experiments(e.id).update(metrics=new_metrics)
      assert updated_e.metrics[0].threshold == 1.23
      assert updated_e.metrics[1].threshold == 4.56
      assert updated_e.metrics[2].threshold is None
      fetched_e = connection.experiments(e.id).fetch()
      assert fetched_e.metrics[0].threshold == 1.23
      assert fetched_e.metrics[1].threshold == 4.56
      assert fetched_e.metrics[2].threshold is None

  def test_update_threshold_on_stored_raises(self, services, connection):
    metrics = [
      {"name": "optimized1"},
      {"name": "optimized2"},
      {"name": "stored", "strategy": MetricStrategyNames.STORE},
    ]
    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = 1.23
      new_metrics[1]["threshold"] = 4.56
      new_metrics[2]["threshold"] = 7.89
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

  def test_update_threshold_on_constraint_metric(self, services, connection):
    metrics = [
      {"name": "constraint", "strategy": MetricStrategyNames.CONSTRAINT, "threshold": 0.1},
      {"name": "optimized1"},
    ]
    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = 4.56
      updated_e = connection.experiments(e.id).update(metrics=new_metrics)
      assert updated_e.metrics[0].threshold == 4.56

  def test_update_remove_threshold_on_constraint_raises(self, services, connection):
    metrics = [
      {"name": "constraint", "strategy": MetricStrategyNames.CONSTRAINT, "threshold": 0.1},
      {"name": "optimized"},
    ]
    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0] = {"name": "constraint", "strategy": MetricStrategyNames.CONSTRAINT}
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

    with connection.create_any_experiment(metrics=metrics, observation_budget=10) as e:
      new_metrics = deepcopy(metrics)
      new_metrics[0]["threshold"] = None
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(metrics=new_metrics)
      fetched_e = connection.experiments(e.id).fetch()
      self._compare_metric_lists(fetched_e.metrics, e.metrics)

  @pytest.mark.parametrize(
    "prior",
    [
      dict(name="normal", mean=0.0, scale=1.0),
      dict(name="beta", shape_a=1.5, shape_b=2.5),
    ],
  )
  def test_parameter_prior_update(
    self,
    connection,
    client_id,
    prior,
  ):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    experiment = connection.clients(client_id).experiments().create(**meta)

    assert experiment.parameters[1].type == "double"
    parameter_json = experiment.parameters[1].to_json()
    assert "prior" in parameter_json
    assert parameter_json["prior"] is None

    new_parameters = deepcopy(meta["parameters"])
    new_parameters[1]["prior"] = prior
    updated_experiment = connection.experiments(experiment.id).update(parameters=new_parameters)

    parameter_json = updated_experiment.parameters[1].to_json()
    assert "prior" in parameter_json
    created_prior = parameter_json["prior"]
    for key, value in prior.items():
      assert created_prior[key] == value

    remove_prior_parameters = deepcopy(new_parameters)
    remove_prior_parameters[1]["prior"] = None
    updated_experiment = connection.experiments(experiment.id).update(parameters=remove_prior_parameters)

    parameter_json = updated_experiment.parameters[1].to_json()
    assert "prior" in parameter_json
    assert parameter_json["prior"] is None

  def test_log_transform_update_errors(self, connection):
    p1 = dict(name="a", type="double", bounds=dict(min=1, max=10), transformation=ParameterTransformationNames.LOG)
    p2 = dict(name="b", type="double", bounds=dict(min=1, max=10))
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [p1, p2]
    e = connection.create_any_experiment(**meta)
    assert e.parameters[0].to_json()["transformation"] == ParameterTransformationNames.LOG

    p1_none_transform = deepcopy(p1)
    p1_none_transform["transformation"] = ParameterTransformationNames.NONE
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[p1_none_transform, p2])

    p2_with_log = deepcopy(p2)
    p2_with_log["transformation"] = ParameterTransformationNames.LOG
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[p1, p2_with_log])

  def test_log_transform_invalid_bounds_errors(self, connection):
    p1 = dict(name="a", type="double", bounds=dict(min=1, max=10), transformation=ParameterTransformationNames.LOG)
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [p1]
    e = connection.create_any_experiment(**meta)

    p1_invalid_bounds = deepcopy(p1)
    p1_invalid_bounds["bounds"] = dict(min=0, max=10)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[p1_invalid_bounds])

  def test_log_transform_invalid_default_value_errors(self, connection):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    e = connection.create_any_experiment(**meta)

    original_parameters = meta["parameters"]
    new_param = dict(
      name="new_p",
      type="double",
      bounds=dict(min=1, max=10),
      transform=ParameterTransformationNames.LOG,
      default_value=0,
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=original_parameters + [new_param])

    new_param["default_value"] = 1
    updated_e = connection.experiments(e.id).update(parameters=original_parameters + [new_param])
    assert len(updated_e.parameters) == len(original_parameters) + 1

  def test_forbid_num_solutions_udpate(self, connection):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    e = connection.create_any_experiment(**meta)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(num_solutions=3)

  def test_update_budget_runs_only(self, connection, project):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    del meta["observation_budget"]
    e = connection.create_any_experiment(runs_only=True, project=project.id, **meta)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(observation_budget=123)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(budget=123, observation_budget=123)

    experiment = connection.experiments(e.id).update(budget=123)
    assert experiment.to_json()["budget"] == 123

  def test_update_project_runs_only(self, connection, project, another_project):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    del meta["observation_budget"]
    e = connection.create_any_experiment(runs_only=True, project=project.id, **meta)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(project=None)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(project=another_project.id)

    connection.experiments(e.id).update(project=project.id)

    assert project.id == connection.experiments(e.id).fetch().project
