# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import time
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import *
from zigopt.handlers.training_runs.parser import MAX_LOG_LENGTH

from integration.base import RaisesApiException
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.test_base import V1Base


TEST_FIELD_VALUES = [
  {"name": "new run"},
  {"favorite": True},
  {"state": "completed"},
  {"state": "failed"},
  {"source_code": {"hash": "abcdef"}},
  {"source_code": {"content": 'print("hello")\n'}},
  {"source_code": {"content": None}},
  {"datasets": {"iris": {}}},
  {"model": {"type": "xgboost"}},
  {"logs": {"stdout": {"content": "abc"}}},
  {"assignments": {"abc": "def", "ghi": 123}},
  {"metadata": {"abc": "def", "ghi": 123}},
  {"values": {}},
  {"values": {"abc": {"value": 2}}},
  {"values": {"abc": {"value": 2, "value_stddev": 0.1}}},
  # Multiple values at once
  {"name": "new run", "state": "completed"},
]

TEST_INVALID_FIELD_VALUES = [
  {"name": None},
  {"name": ""},
  {"name": 1},
  {"favorite": "nope"},
  {"state": None},
  {"state": "broken"},
  {"state": 1},
  {"source_code": {"hash": 123}},
  {"source_code": {"content": 123}},
  {"source_code": []},
  {"values": []},
]


def assert_json_contains(key, value):
  if is_mapping(key):
    assert is_mapping(value)
    for k in value:
      assert_json_contains(key[k], value[k])
  elif is_sequence(key):
    assert is_sequence(value)
    assert len(key) == len(value)
    for k, v in zip(key, value):
      assert_json_contains(k, v)
  else:
    assert key == value


class TestTrainingRunsUpdate(V1Base, TrainingRunTestMixin):
  @pytest.mark.parametrize("fields", TEST_FIELD_VALUES)
  def test_create_fields(self, connection, fields, project):
    kwargs = extend_dict({"name": "run"}, fields)
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(**kwargs)
    for key, value in fields.items():
      assert_json_contains(training_run.to_json()[key], value)
      assert_json_contains(connection.training_runs(training_run.id).fetch().to_json()[key], value)

  @pytest.mark.parametrize("fields", TEST_INVALID_FIELD_VALUES)
  def test_create_invalid_fields(self, connection, fields, project):
    kwargs = extend_dict({"name": "run"}, fields)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).training_runs().create(**kwargs)

  @pytest.mark.parametrize("fields", TEST_FIELD_VALUES)
  def test_update_fields(self, connection, fields, training_run):
    updated_training_run = connection.training_runs(training_run.id).update(**fields)
    for key, value in fields.items():
      assert_json_contains(updated_training_run.to_json()[key], value)
      assert_json_contains(connection.training_runs(updated_training_run.id).fetch().to_json()[key], value)

  @pytest.mark.parametrize("fields", TEST_INVALID_FIELD_VALUES)
  def test_update_invalid_fields(self, connection, fields, training_run):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(training_run.id).update(**fields)

  @pytest.mark.parametrize(
    "fields",
    [
      {"assignments": None},
      {"logs": None},
      {"values": None},
    ],
  )
  def test_remove_field(self, connection, fields, project):
    training_run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(
        name="run",
        assignments={"a": 2},
        logs={"stdout": {"content": "abc"}},
        values={"abc": {"value": 2}},
      )
    )
    for key in fields:
      assert bool(training_run.to_json().get(key))
    training_run = connection.training_runs(training_run.id).update(**fields)
    for key in fields:
      assert not bool(training_run.to_json().get(key))

  @pytest.mark.parametrize(
    "key, value, new_value",
    [
      ("assignments", {"a": "b"}, {"c": "d"}),
      ("metadata", {"a": 1}, {"c": 2}),
      ("logs", {"stdout": {"content": ""}}, {"stderr": {"content": "text"}}),
      ("values", {"a": {"value": 2}}, {"b": {"value": 10}}),
    ],
  )
  def test_merge(self, connection, project, key, value, new_value):
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")

    connection.training_runs(training_run.id).merge(**{key: {}})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), {})

    connection.training_runs(training_run.id).merge(**{key: value})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), value)
    connection.training_runs(training_run.id).merge(**{key: {}})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), value)
    connection.training_runs(training_run.id).merge(**{key: value})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), value)

    merged_values = extend_dict({}, value, new_value)
    connection.training_runs(training_run.id).merge(**{key: new_value})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), merged_values)
    connection.training_runs(training_run.id).merge(**{key: value})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), merged_values)
    connection.training_runs(training_run.id).merge(**{key: new_value})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), merged_values)
    connection.training_runs(training_run.id).merge(**{key: merged_values})
    assert_json_contains(getattr(connection.training_runs(training_run.id).fetch(), key), merged_values)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(training_run.id).merge(**{key: 1})

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(training_run.id).merge(**{key: []})

  def test_merge_primitive_value(self, connection, project):
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")
    assert connection.training_runs(training_run.id).merge(name="new name").name == "new name"
    assert connection.training_runs(training_run.id).merge(model={"type": "xgboost"}).model.type == "xgboost"

  def test_merge_no_response(self, connection, project):
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")
    connection.conn.driver.default_headers["X-Response-Content"] = "skip"
    assert connection.training_runs(training_run.id).merge(name="new name") is None
    del connection.conn.driver.default_headers["X-Response-Content"]
    assert connection.training_runs(training_run.id).fetch().name == "new name"

  def test_complete_sets_completed_time(self, connection, training_run):
    now = unix_timestamp()
    assert training_run.completed is None
    training_run = connection.training_runs(training_run.id).update(state="completed")
    assert training_run.completed >= now

  def test_updated_time(self, connection, training_run):
    now = training_run.updated
    time.sleep(1)
    connection.training_runs(training_run.id).update(name="new run")
    assert connection.training_runs(training_run.id).fetch().updated > now

  def test_cant_update_experiment(self, connection, training_run, project):
    experiment = connection.create_any_experiment(project=project.id)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(training_run.id).update(experiment=experiment.id)

  def test_update_project_id(self, connection, project, training_run):
    new_project_id = "new-project"
    connection.clients(connection.client_id).projects().create(name="new project", id=new_project_id)
    updated_training_run = connection.training_runs(training_run.id).update(project=new_project_id)
    assert updated_training_run.project == new_project_id
    assert connection.training_runs(training_run.id).fetch().project == new_project_id
    assert training_run.id in [
      run.id
      for run in connection.clients(connection.client_id)
      .projects(new_project_id)
      .training_runs()
      .fetch()
      .iterate_pages()
    ]

  def test_invalid_project_id(self, connection, project, training_run):
    new_project_id = "some-fake-project"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(training_run.id).update(project=new_project_id)

  def test_update_project_id_with_experiment(self, connection, project, training_run):
    new_project_id = "new-project"
    connection.clients(connection.client_id).projects().create(name="new project", id=new_project_id)
    updated_training_run = connection.training_runs(training_run.id).update(project=new_project_id)
    assert updated_training_run.project == new_project_id
    assert connection.training_runs(training_run.id).fetch().project == new_project_id
    assert training_run.id in [
      run.id
      for run in connection.clients(connection.client_id)
      .projects(new_project_id)
      .training_runs()
      .fetch()
      .iterate_pages()
    ]

  def test_update_logs_truncated(self, connection, training_run):
    long_log = "a" * (MAX_LOG_LENGTH * 2)
    log_field = {"logs": {"stdout": {"content": long_log}}}
    updated_training_run = connection.training_runs(training_run.id).update(**log_field)
    assert len(updated_training_run.to_json()["logs"]["stdout"]["content"]) == MAX_LOG_LENGTH
    assert (
      len(connection.training_runs(updated_training_run.id).fetch().to_json()["logs"]["stdout"]["content"])
      == MAX_LOG_LENGTH
    )


class TestChangeRunState(V1Base, TrainingRunTestMixin):
  @pytest.fixture
  def merge_connection(self, connection):
    # patches the connection object so that update (PUT) is converted to MERGE
    original_request = connection.driver.request

    def request(method, *args, **kwargs):
      if method.lower() == "put":
        method = "MERGE"
      return original_request(method, *args, **kwargs)

    connection.driver.request = request
    return connection

  @pytest.mark.parametrize(
    "assignments_update",
    [
      {"{}": 1},
      {"{'}": 1},
      {'{"}': 1},
      {"{'\"}": 1},
      {"{'\"\\}": 1},
    ],
  )
  def test_update_assignments(self, merge_connection, project, assignments_update):
    run = merge_connection.clients(project.client).projects(project.id).training_runs().create(name="test update run")
    run = merge_connection.training_runs(run.id).update(assignments=assignments_update)
    assert run.to_json()["assignments"] == assignments_update

  @pytest.mark.parametrize(
    "metadata_update",
    [
      {"{}": 1},
      {"{'}": 1},
      {'{"}': 1},
      {"{'\"}": 1},
      {"{'\"\\}": 1},
    ],
  )
  def test_update_metadata(self, merge_connection, project, metadata_update):
    run = merge_connection.clients(project.client).projects(project.id).training_runs().create(name="test update run")
    run = merge_connection.training_runs(run.id).update(metadata=metadata_update)
    assert run.to_json()["metadata"] == metadata_update

  @pytest.mark.parametrize(
    "dataset_update",
    [
      {"{}": {}},
      {"{'}": {}},
      {'{"}': {}},
      {"{'\"}": {}},
      {"{'\"\\}": {}},
    ],
  )
  def test_update_datasets(self, merge_connection, project, dataset_update):
    run = merge_connection.clients(project.client).projects(project.id).training_runs().create(name="test update run")
    run = merge_connection.training_runs(run.id).update(datasets=dataset_update)
    assert run.to_json()["datasets"].keys() == dataset_update.keys()

  @pytest.mark.parametrize(
    "values_update",
    [
      {"{}": {"value": 1}},
      {"{'}": {"value": 1}},
      {'{"}': {"value": 1}},
      {"{'\"}": {"value": 1}},
      {"{'\"\\}": {"value": 1}},
    ],
  )
  def test_update_values(self, merge_connection, project, values_update):
    run = merge_connection.clients(project.client).projects(project.id).training_runs().create(name="test update run")
    run = merge_connection.training_runs(run.id).update(values=values_update)
    assert run.to_json()["values"][next(iter(values_update))]["value"] == 1

  def test_update_delete_field(self, connection, project):
    run = connection.clients(project.client).projects(project.id).training_runs().create(name="test update run")
    run = connection.training_runs(run.id).update(deleted=True)
    assert run.deleted is True
    run = connection.training_runs(run.id).update(deleted=False)
    assert run.deleted is False

  def test_update_delete_field_cascades_to_suggestions(self, connection, project, aiexperiment_in_project, services):
    aiexperiment = aiexperiment_in_project
    run = (
      connection.aiexperiments(aiexperiment.id)
      .training_runs()
      .create(
        name="test update run",
      )
    )
    db_training_run = services.training_run_service.find_by_id(int(run.id))
    db_suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    assert db_suggestion
    connection.training_runs(run.id).update(deleted=True)
    db_suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    assert db_suggestion is None
    connection.training_runs(run.id).update(deleted=False)
    db_suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    assert db_suggestion

  def test_update_delete_field_cascades_to_observations(self, connection, project, aiexperiment_in_project, services):
    aiexperiment = aiexperiment_in_project
    run = connection.aiexperiments(aiexperiment.id).training_runs().create(name="test update run")
    connection.training_runs(run.id).update(state="failed")
    db_training_run = services.training_run_service.find_by_id(int(run.id))
    db_observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert db_observation
    connection.training_runs(run.id).update(deleted=True)
    db_observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert db_observation is None
    connection.training_runs(run.id).update(deleted=False)
    db_observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert db_observation
