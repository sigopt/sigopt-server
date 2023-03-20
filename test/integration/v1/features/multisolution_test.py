# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.base import RaisesApiException
from integration.utils.random_assignment import random_assignments
from integration.v1.constants import EXPERIMENT_META_MULTISOLUTION, EXPERIMENT_META_WITH_CONSTRAINTS
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase


class MultisolutionExperimentTestBase(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self):
    meta = copy.deepcopy(EXPERIMENT_META_MULTISOLUTION)
    return meta


class TestCreateMultisolutionExperiment(MultisolutionExperimentTestBase):
  def test_experiment_create_meta(self, connection, client_id, meta):
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id is not None
    assert e.type == "offline"
    assert e.observation_budget is not None

  def test_multisolution_create_with_store_metric(self, connection):
    num_solutions = 5
    observation_budget = 10
    e = connection.create_any_experiment(
      metrics=[
        dict(name="optimization"),
        dict(name="store", strategy="store"),
      ],
      observation_budget=observation_budget,
      num_solutions=num_solutions,
    )
    assert e.id
    assert e.type == "offline"
    assert e.observation_budget == observation_budget

  def test_multisolution_create_with_constraint_metrics(self, connection):
    num_solutions = 5
    observation_budget = 10
    e = connection.create_any_experiment(
      metrics=[
        dict(name="optimization"),
        dict(name="constraint-1", strategy="constraint", threshold=0.2),
        dict(name="constraint-2", strategy="constraint", threshold=0.2),
        dict(name="store", strategy="store"),
      ],
      observation_budget=observation_budget,
      num_solutions=num_solutions,
    )
    assert e.id
    assert e.type == "offline"
    assert e.observation_budget == observation_budget

  def test_multisolution_create_with_parameter_constraints(self, connection, client_id, services):
    meta = copy.deepcopy(EXPERIMENT_META_WITH_CONSTRAINTS)
    meta["num_solutions"] = 5
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id
    assert e.type == "offline"
    assert e.num_solutions == 5

    num_obs = 16
    suggestions = []
    observations = []
    for _ in range(num_obs):
      suggestions.append(connection.experiments(e.id).suggestions().create())
      observations.append(
        {
          "suggestion": suggestions[-1].id,
          "values": [dict(name="profit", value=0)],
        }
      )
    self.batch_upload_observations(e, observations, no_optimize=False)

    suggestion = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.SEARCH

  def test_multisolution_create_threshold_on_optimized_metric(self, connection):
    num_solutions = 5
    observation_budget = 10
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="optimization", threshold=0.2),
          dict(name="constraint-1", strategy="constraint", threshold=0.2),
          dict(name="constraint-2", strategy="constraint", threshold=0.2),
        ],
        observation_budget=observation_budget,
        num_solutions=num_solutions,
      )

  def test_multisolution_create_no_optimized_metric(self, connection):
    num_solutions = 5
    observation_budget = 10
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="constraint-1", strategy="constraint", threshold=0.2),
        ],
        observation_budget=observation_budget,
        num_solutions=num_solutions,
      )

  def test_multisolution_create_fails_conditionals(self, connection, client_id, meta):
    meta["parameters"][1] = {
      "name": "b",
      "type": "double",
      "bounds": {"min": -50, "max": 0},
      "conditions": {"x": ["5", "10"]},
    }
    meta["conditionals"] = [{"name": "x", "values": ["1", "5", "10"]}]
    assert meta["num_solutions"] > 1
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_multisolution_fails_multi_task(self, connection, client_id, meta):
    meta["tasks"] = [
      {"name": "cheapest", "cost": 0.1},
      {"name": "cheaper", "cost": 0.3},
      {"name": "expensive", "cost": 1.0},
    ]
    assert meta["num_solutions"] > 1
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_default_num_solutions(self, connection, client_id, meta, services):
    del meta["num_solutions"]
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.num_solutions is None
    zigopt_experiment = services.experiment_service.find_by_id(e.id)
    assert zigopt_experiment.num_solutions == 1

  @pytest.mark.parametrize("observation_budget", [None, -1000])
  def test_invalid_budget(self, connection, client_id, meta, observation_budget):
    meta.update(observation_budget=observation_budget)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  @pytest.mark.parametrize("num_solutions", [-1, "a"])
  def test_invalid_num_solutions(self, connection, client_id, meta, num_solutions):
    meta.update(num_solutions=num_solutions)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  @pytest.mark.parametrize("extra_solutions", [1, 5, 10])
  def test_num_solutions_too_large(self, connection, client_id, meta, extra_solutions):
    num_solutions = meta["observation_budget"] + extra_solutions
    meta.update(num_solutions=num_solutions)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_update_budget(self, connection, meta):
    # Cannot change the budget for a multisolution experiment
    with connection.create_any_experiment(**meta) as e:
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(e.id).update(observation_budget=meta["observation_budget"] + 1)


class TestMultisolutionExperiment(MultisolutionExperimentTestBase):
  @pytest.mark.parametrize("num_observations", [2, 12, 18])
  @pytest.mark.parametrize("num_solutions", [7, 14])
  @pytest.mark.parametrize("observation_budget", [15, 21])
  def test_large_num_solutions(
    self,
    connection,
    client_id,
    num_observations,
    num_solutions,
    observation_budget,
  ):
    meta = copy.deepcopy(EXPERIMENT_META_MULTISOLUTION)
    meta["num_solutions"] = num_solutions
    meta["observation_budget"] = observation_budget
    e = connection.clients(client_id).experiments().create(**meta)

    assert meta["parameters"][0]["name"] == "a"
    a_max = meta["parameters"][0]["bounds"]["max"]
    a_min = meta["parameters"][0]["bounds"]["min"]
    assert meta["parameters"][1]["name"] == "b"
    b_max = meta["parameters"][1]["bounds"]["max"]
    b_min = meta["parameters"][1]["bounds"]["min"]
    assert meta["parameters"][2]["name"] == "c"
    assert meta["parameters"][2]["categorical_values"][0]["name"] == "d"
    assert meta["parameters"][2]["categorical_values"][1]["name"] == "e"

    for i in range(num_observations):
      connection.experiments(e.id).observations().create(
        assignments={
          "a": int(a_min + (a_max - a_min) * i / num_observations),
          "b": b_min + (b_max - b_min) * i / num_observations,
          "c": "d" if i % 2 == 0 else "e",
        },
        values=[{"value": i}],
        no_optimize=True,
      )
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == min(num_solutions, num_observations)

  @pytest.mark.parametrize("objective", ["maximize", "minimize"])
  @pytest.mark.parametrize("num_extra_observations", [7, 21])
  def test_best_assignments(self, connection, client_id, meta, objective, num_extra_observations):
    best_value, worst_value = (0.0, 1.0) if objective == "minimize" else (1.0, 0.0)

    meta["metrics"][0]["objective"] = objective
    e = connection.clients(client_id).experiments().create(**meta)

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 0

    connection.experiments(e.id).observations().create(
      assignments={"a": 1, "b": 0, "c": "d"},
      values=[{"value": best_value}],
      no_optimize=True,
    )

    # Only return a single assignment since there has only been one observation
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 1
    for data in a.data:
      assert data.values[0].value == best_value

    # Add an observation that is sufficiently far away from the other best observation
    connection.experiments(e.id).observations().create(
      assignments={"a": -50, "b": 50, "c": "e"},
      values=[{"value": best_value}],
      no_optimize=True,
    )

    # Add observations with bad values
    for _ in range(num_extra_observations):
      connection.experiments(e.id).observations().create(
        assignments=random_assignments(e),
        values=[{"value": worst_value}],
        no_optimize=True,
      )

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 2
    for data in a.data:
      assert data.values[0].value == best_value
      assert data.id is not None

  @pytest.mark.parametrize("objective", ["maximize", "minimize"])
  def test_best_assignments_unique_assignments(self, connection, client_id, meta, objective):
    num_extra_observations = 9
    best_value, worst_value = (0.0, 1.0) if objective == "minimize" else (1.0, 0.0)
    meta["metrics"][0]["objective"] = objective
    e = connection.clients(client_id).experiments().create(**meta)

    # Add duplicated solution
    for _ in range(2):
      connection.experiments(e.id).observations().create(
        assignments={"a": 1, "b": 0, "c": "d"},
        values=[{"value": best_value}],
        no_optimize=True,
      )

    # Add an observation that is sufficiently far away from the other best observation
    connection.experiments(e.id).observations().create(
      assignments={"a": -50, "b": 50, "c": "e"},
      values=[{"value": best_value}],
      no_optimize=True,
    )

    # Add observations with bad values
    for _ in range(num_extra_observations):
      connection.experiments(e.id).observations().create(
        assignments=random_assignments(e),
        values=[{"value": worst_value}],
        no_optimize=True,
      )

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 2
    best_solutions_assignments = set()
    for data in a.data:
      assert data.values[0].value == best_value
      assert data.id is not None
      assignment_set = frozenset(data.assignments.items())
      assert assignment_set not in best_solutions_assignments
      best_solutions_assignments.add(assignment_set)

  @pytest.mark.parametrize("objective", ["maximize", "minimize"])
  @pytest.mark.parametrize("num_extra_observations", [0, 5, 13])
  @pytest.mark.parametrize("num_solutions", [2, 7, 11])
  def test_best_assignments_categoricals(
    self,
    connection,
    client_id,
    meta,
    num_extra_observations,
    num_solutions,
    objective,
  ):
    meta["num_solutions"] = num_solutions
    meta["metrics"][0]["objective"] = objective
    best_value, worst_value = (-1.0, 1.0) if objective == "minimize" else (1.0, -1.0)
    e = connection.clients(client_id).experiments().create(**meta)
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 0, "No observations yet"

    best_assignments_a = {"a": 1, "b": 0, "c": "d"}
    best_assignments_b = {"a": -50, "b": 50, "c": "e"}
    bad_assignment = {"a": 0, "b": 1, "c": "d"}

    connection.experiments(e.id).observations().create(
      assignments=best_assignments_a,
      values=[{"value": best_value}],
      no_optimize=True,
    )

    # Only return a single assignment since there has only been one observation
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 1
    for data in a.data:
      assert data.values[0].value == best_value

    # Add an observation that is sufficiently far away from the other best observation
    connection.experiments(e.id).observations().create(
      assignments=best_assignments_b,
      values=[{"value": 2 * best_value}],
      no_optimize=True,
    )

    # Extra worthless observations
    for _ in range(num_extra_observations):
      connection.experiments(e.id).observations().create(
        assignments=bad_assignment,
        values=[{"value": worst_value}],
        no_optimize=True,
      )

    a = connection.experiments(e.id).best_assignments().fetch()
    total_observations = num_extra_observations + 2
    assert a.count == min(num_solutions, total_observations)
    assert a.data[0].values[0].value == 2 * best_value
    assert a.data[0].assignments.items() == best_assignments_b.items()
    assert a.data[1].values[0].value == best_value
    assert a.data[1].assignments.items() == best_assignments_a.items()

  def test_best_assignments_with_failures(
    self,
    connection,
    client_id,
    meta,
    services,
  ):
    num_solutions = 5
    meta["num_solutions"] = num_solutions
    meta["metrics"][0]["objective"] = "maximize"
    best_value, worst_value = (1.0, -1.0)

    e = connection.clients(client_id).experiments().create(**meta)
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 0, "No observations yet"

    best_assignments_d = {"a": 1, "b": 0, "c": "d"}
    best_assignments_e = {"a": -50, "b": 50, "c": "e"}
    bad_assignment = {"a": 0, "b": 1, "c": "d"}

    observations = [{"assignments": bad_assignment, "failed": True} for _ in range(30)]
    self.batch_upload_observations(e, observations, no_optimize=False)

    suggestion = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
    assert (
      unprocessed_suggestion.source != UnprocessedSuggestion.Source.SEARCH
    ), "Should not call search with all failures"

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 0, "All failures!"

    connection.experiments(e.id).observations().create(
      assignments=best_assignments_d,
      values=[{"value": best_value}],
      no_optimize=True,
    )
    # Only return a single assignment since there has only been one observation
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 1
    for data in a.data:
      assert data.values[0].value == best_value

    # Add an observation that is sufficiently far away from the other best observation
    connection.experiments(e.id).observations().create(
      assignments=best_assignments_e,
      values=[{"value": 2 * best_value}],
      no_optimize=True,
    )

    # Extra worthless observations
    num_obs = 16
    suggestions = []
    observations = []
    for _ in range(num_obs):
      suggestions.append(connection.experiments(e.id).suggestions().create())
      observations.append(
        {
          "suggestion": suggestions[-1].id,
          "values": [dict(name="profit", value=worst_value)],
        }
      )
    self.batch_upload_observations(e, observations, no_optimize=False)

    suggestion = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.SEARCH

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == num_solutions
    assert a.data[0].values[0].value == 2 * best_value
    assert a.data[0].assignments.items() == best_assignments_e.items()
    assert a.data[1].values[0].value == best_value
    assert a.data[1].assignments.items() == best_assignments_d.items()
    assert all(isinstance(a.data[i].values[0].value, float) for i in range(num_solutions))
