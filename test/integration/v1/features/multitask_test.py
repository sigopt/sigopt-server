# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import numpy
import pytest

from zigopt.common import *

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class MultitaskExperimentsTestBase(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  experiment_meta = {
    "name": "multitask experiment",
    "parameters": [
      {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
      {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
      {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
    ],
    "tasks": [
      {"name": "cheapest", "cost": 0.1},
      {"name": "cheaper", "cost": 0.3},
      {"name": "expensive", "cost": 1.0},
    ],
    "observation_budget": 60,
  }


class TestCreateMultitaskExperiments(MultitaskExperimentsTestBase):
  def test_experiment_create(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    assert e.id is not None
    assert e.type == "offline"
    assert e.observation_budget is not None
    assert e.tasks is not None and len(e.tasks) == 3

  def test_experiment_create_needs_budget(self, connection, client_id):
    no_budget = omit(self.experiment_meta, "observation_budget")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**no_budget)

  def test_experiment_create_only_one_task(self, connection, client_id):
    one_task = omit(self.experiment_meta, "tasks")
    one_task["tasks"] = [{"name": "only task", "cost": 1.0}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**one_task)

  def test_experiment_create_incomplete_tasks(self, connection, client_id):
    missing_costs = omit(self.experiment_meta, "tasks")
    missing_costs["tasks"] = [{"name": "task"}, {"name": "other task"}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**missing_costs)
    missing_costs["tasks"] = [{"cost": 0.3}, {"cost": 1.0}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**missing_costs)

  def test_experiment_create_duplicate_tasks(self, connection, client_id):
    new_meta = omit(self.experiment_meta, "tasks")
    new_meta["tasks"] = [{"name": "task", "cost": 1.0}, {"name": "task", "cost": 0.3}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)
    new_meta["tasks"] = [
      {"name": "task", "cost": 0.3},
      {"name": "other task", "cost": 0.3},
      {"name": "other other task", "cost": 1.0},
    ]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)

  def test_experiment_create_with_bad_costs(self, connection, client_id):
    new_meta = omit(self.experiment_meta, "tasks")
    new_meta["tasks"] = [{"name": "task", "cost": 0.5}, {"name": "task 2", "cost": 0.3}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)
    new_meta["tasks"] = [{"name": "task", "cost": 1.0}, {"name": "task 2", "cost": 1.0}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)
    new_meta["tasks"] = [{"name": "task", "cost": 1.0}, {"name": "task 2", "cost": 0.0}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)
    new_meta["tasks"] = [{"name": "task", "cost": 1.0}, {"name": "task 2", "cost": -0.1}]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**new_meta)


class TestRunMultitaskExperiments(MultitaskExperimentsTestBase):
  def test_experiment_cycle(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    assert e.id is not None
    assert e.type == "offline"
    assert e.observation_budget is not None
    assert e.tasks is not None and len(e.tasks) == 3
    assert [t.name is not None and t.cost is not None for t in e.tasks]

    s = connection.experiments(e.id).suggestions().create()
    assert s.task.name in [t.name for t in e.tasks]
    o = connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0.1}])
    assert o.task == s.task

  def test_observation_creation(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)

    s = connection.experiments(e.id).suggestions().create()
    connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0.1}])
    for t in e.tasks:
      o = connection.experiments(e.id).observations().create(assignments=s.assignments, values=[{"value": 0.1}], task=t)
      assert o.task == t
    o = (
      connection.experiments(e.id)
      .observations()
      .create(assignments=s.assignments, values=[{"value": 0.1}], task=e.tasks[0].name)
    )
    assert o.task == e.tasks[0]

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(assignments=s.assignments, values=[{"value": 0.1}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(task=e.tasks[0], values=[{"value": 0.1}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(assignments=s.assignments, task=e.tasks[0])

  def test_observation_creation_with_parameter_constraints(self, connection, client_id):
    meta = self.experiment_meta.copy()
    meta["linear_constraints"] = [
      {
        "type": "less_than",
        "threshold": 40,
        "terms": [{"name": "a", "weight": 1}, {"name": "b", "weight": 1}],
      }
    ]
    meta["parameters"] = [
      {"name": "a", "type": "double", "bounds": {"min": 1, "max": 50}},
      {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
      {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
    ]
    e = connection.clients(client_id).experiments().create(**meta)

    observations = []
    for _ in range(10):
      a = numpy.random.uniform(1, 35)
      b = numpy.random.uniform(-50, 0)
      c = numpy.random.choice(["d", "e"])
      observations.append(
        {
          "assignments": {"a": a, "b": b, "c": c},
          "values": [{"value": numpy.random.random()}],
          "task": numpy.random.choice(["cheapest", "cheaper", "expensive"]),
        }
      )
    self.batch_upload_observations(e, observations)

    connection.experiments(e.id).suggestions().create()

  def test_best_assignments(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    s1 = connection.experiments(e.id).suggestions().create()

    s2 = connection.experiments(e.id).suggestions().create(assignments=s1.assignments, task="cheapest")
    connection.experiments(e.id).observations().create(suggestion=s2.id, values=[{"value": 0.1}])
    best_assignments = connection.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 0

    s3 = connection.experiments(e.id).suggestions().create(assignments=s1.assignments, task="expensive")
    connection.experiments(e.id).observations().create(suggestion=s3.id, values=[{"value": 0.5}])
    best_assignments = connection.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 1
    assert best_assignments.data[0].values[0].value == 0.5


class TestUpdateMultitaskExperiments(MultitaskExperimentsTestBase):
  def test_cannot_update_experiment_tasks(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    assert e.observation_budget == 60
    e = connection.experiments(e.id).update(observation_budget=100)
    assert e.observation_budget == 100
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(  # Update on tasks is totally disallowed, even for a no-op situation
        tasks=[
          {"name": "cheapest", "cost": 0.1},
          {"name": "cheaper", "cost": 0.3},
          {"name": "expensive", "cost": 1.0},
        ],
      )


class TestMultitaskExperimentSuggestions(MultitaskExperimentsTestBase):
  def test_suggestions_are_mutable(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)

    s = connection.experiments(e.id).suggestions().create()
    connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0.1}])

    # Update is a no-op and only allows updating metadata
    s_update = connection.experiments(e.id).suggestions(s.id).update(task="cheapest")
    assert s_update.task == s.task

    connection.experiments(e.id).suggestions(s.id).delete()
    assert connection.experiments(e.id).suggestions().fetch().count == 0

  def test_suggestions_can_be_created_and_queued(self, connection, client_id):
    # TODO: Figure out queued_suggestion object wrt the client????
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)

    s = connection.experiments(e.id).suggestions().create()
    assert connection.experiments(e.id).suggestions().fetch().count == 1
    s2 = connection.experiments(e.id).suggestions().create(assignments=s.assignments, task=s.task)
    assert connection.experiments(e.id).suggestions().fetch().count == 2
    assert s.assignments == s2.assignments and s.task == s2.task and s.id != s2.id

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).suggestions().create(assignments=s.assignments)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).suggestions().create(assignments=s.assignments, task="cheapy")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).suggestions().create(task="cheaper")

    connection.experiments(e.id).suggestions().delete()
    qs = connection.experiments(e.id).queued_suggestions().create(assignments=s.assignments, task=s.task)
    assert connection.experiments(e.id).suggestions().fetch().count == 0
    assert s.assignments == qs.assignments and s.task.name == qs.to_json()["task"]["name"]
    s3 = connection.experiments(e.id).suggestions().create()
    assert connection.experiments(e.id).suggestions().fetch().count == 1
    assert s3.assignments == qs.assignments and s3.task.name == qs.to_json()["task"]["name"]

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).queued_suggestions().create(task=s.task)


class TestMultitaskExperimentObservations(MultitaskExperimentsTestBase):
  def test_manually_create_observations(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    s = connection.experiments(e.id).suggestions().create()

    o = (
      connection.experiments(e.id)
      .observations()
      .create(assignments=s.assignments, task=s.task, values=[{"value": 0.1}])
    )
    assert o.assignments == s.assignments and o.task == s.task and o.values[0].value == 0.1

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(task=s.task, values=[{"value": 0.1}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(assignments=s.assignments, values=[{"value": 0.1}])

  def test_update_observations(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)

    s = connection.experiments(e.id).suggestions().create()
    o = connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0.1}])
    assert o.values[0].value == 0.1

    o_up = connection.experiments(e.id).observations(o.id).update(values=[{"value": 0.2}])
    assert o.id == o_up.id and o_up.values[0].value == 0.2

    s2 = connection.experiments(e.id).suggestions().create()
    o2 = connection.experiments(e.id).observations().create(suggestion=s2.id, values=[{"value": 0.3}])
    assert o2.suggestion != o.suggestion

    o2_up = connection.experiments(e.id).observations(o2.id).update(suggestion=s.id)
    assert o2.id == o2_up.id and o.id != o2_up.id and o2_up.values[0].value == 0.3 and o2_up.suggestion == o.suggestion

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(task=s.task.name)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(suggestion=s.id, task=s.task)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(assignments=s.assignments)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(suggestion=None, assignments=s.assignments)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(
        suggestion=None, assignments=s.assignments, values=[{"value": -1}]
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations(o.id).update(suggestion=None, task=s.task, values=[{"value": -1}])

    x = {"a": 58, "b": -12.3456, "c": "d"}
    o3 = (
      connection.experiments(e.id)
      .observations(o.id)
      .update(
        suggestion=None,
        assignments=x,
        task="cheaper",
        values=[{"value": 0.4}],
      )
    )
    assert o.id == o3.id and o3.values[0].value == 0.4 and o3.assignments.to_json() == x and o3.task.name == "cheaper"

    o4 = (
      connection.experiments(e.id)
      .observations()
      .create(assignments=o3.assignments, task=o3.task, values=[{"value": 0.5}])
    )
    assert o4.assignments == o3.assignments and o4.task == o3.task and o4.values[0].value == 0.5
    o4 = connection.experiments(e.id).observations(o4.id).update(task="expensive")
    assert o4.assignments == o3.assignments and o4.task.name == "expensive" and o4.values[0].value == 0.5
    o4 = connection.experiments(e.id).observations(o4.id).update(assignments=o.assignments)
    assert o4.assignments == o.assignments and o4.task.name == "expensive" and o4.values[0].value == 0.5
    o4 = connection.experiments(e.id).observations(o4.id).update(assignments=x, task="cheapest")
    assert o4.assignments.to_json() == x and o4.task.name == "cheapest" and o4.values[0].value == 0.5

    assert connection.experiments(e.id).observations().fetch().count == 3
    assert connection.experiments(e.id).suggestions().fetch().count == 2
    assert connection.experiments(e.id).suggestions().fetch(state="open").count == 1
    connection.experiments(e.id).suggestions().delete()
    assert connection.experiments(e.id).suggestions().fetch().count == 0

    assert connection.experiments(e.id).observations().fetch().count == 3
    connection.experiments(e.id).observations().delete()
    assert connection.experiments(e.id).observations().fetch().count == 0
    assert connection.experiments(e.id).observations().fetch(deleted=True).count == 3
