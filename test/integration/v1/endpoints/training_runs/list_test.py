# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
import json
import random
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import *
from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.project.model import Project
from zigopt.protobuf.dict import dict_to_protobuf_struct
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import *
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion
from zigopt.training_run.model import TrainingRun
from zigopt.user.model import User

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base, V1Connection


# NOTE: Fields that are defined on all Training Runs one gets from a API request
INVARIABLY_DEFINED_FIELDS = {
  "id",
  "created",
  "updated",
  "deleted",
  "project",
  "client",
  "state",
  "checkpoint_count",
  "optimized_suggestion",
}

STRING_FIELDS = [
  "assignments.string_key",
  "logs.string_key.content",
  "metadata.string_key",
  "model.type",
  "source_code.content",
  "source_code.hash",
]

DATE_FIELDS = [
  "completed",
  "created",
  "updated",
]

ID_FIELDS = [
  # (API name, DB name, Class)
  ("id", "id", TrainingRun),
  ("experiment", "experiment_id", Experiment),
  ("observation", "observation_id", Observation),
  ("user", "created_by", User),
]

NUMERIC_FIELDS = [
  "assignments.double_key",
  "metadata.double_key",
  "values.string_key.value",
  "values.string_key.value_stddev",
]

TEST_VALUES_COUNT = 5
TIMES = [current_datetime() - datetime.timedelta(seconds=s) for s in range(TEST_VALUES_COUNT)]

TRAINING_RUN_TESTABLE_PRIMITIVE_ID_FIELDS = (
  # (API name, DB name, Model)
  ("experiment", "experiment_id", Experiment),
  ("suggestion", "suggestion_id", UnprocessedSuggestion),
  ("observation", "observation_id", Observation),
  ("user", "created_by", User),
)
TRAINING_RUN_TESTABLE_PRIMITIVE_VALUE_FIELDS = (
  # (API name, DB name, values)
  ("created", "created", TIMES),
  ("updated", "updated", TIMES),
  ("completed", "completed", TIMES),
  ("deleted", "deleted", [True, False]),
)

TRAINING_RUN_TESTABLE_PROTOBUF_FIELDS_WITH_VALUES = (
  # (API name, DB name, values)
  # primitive fields
  ("name", "name", [random_string(str_length=6) for _ in range(4)]),
  ("favorite", "favorite", [True, False]),
  # struct fields
  (
    "metadata.metadata_string",
    "metadata",
    [dict_to_protobuf_struct({"metadata_string": random_string()}) for _ in range(4)],
  ),
  (
    "assignments.rate",
    "assignments_struct",
    [dict_to_protobuf_struct({"rate": 100 * random.random()}) for _ in range(4)],
  ),
  (
    "source_code.hash",
    "source_code",
    [SourceCode(hash=random_string(str_length=10)) for _ in range(4)],
  ),
  (
    "model.type",
    "training_run_model",
    [TrainingRunModel(type=random_string(str_length=4)) for _ in range(4)],
  ),
  # map fields
  (
    "logs.my_log.content",
    "logs",
    [{"my_log": Log(content=random_string(str_length=10))} for _ in range(4)],
  ),
  (
    "values.accuracy.value",
    "values_map",
    [{"accuracy": TrainingRunValue(value=100 * random.random())} for _ in range(4)],
  ),
)


def set_string_clause(key, value):
  if not key:
    return value
  parts = key.split(".", 1)
  head = parts[0]
  tail_ = list_get(parts, 1)
  adjacent_values = {}
  if head == "value_stddev":
    adjacent_values["value"] = 1.0
  return {head: set_string_clause(tail_, value), **adjacent_values}


def get_json_key(obj, key):
  def recurse(obj, key):
    if not key:
      return obj
    parts = key.split(".", 1)
    head = parts[0]
    tail_ = list_get(parts, 1)
    return recurse(obj[head], tail_)

  return recurse(obj.to_json(), key)


def equals(field, v):
  return dict(filters=json.dumps([{"field": field, "value": v, "operator": "=="}]))


def less_than(field, v):
  return dict(filters=json.dumps([{"field": field, "value": v, "operator": "<"}]))


def less_than_or_equal(field, v):
  return dict(filters=json.dumps([{"field": field, "value": v, "operator": "<="}]))


def is_null(field):
  return dict(filters=json.dumps([{"field": field, "operator": "isnull"}]))


class TestTrainingRunsList(V1Base):
  # pylint: disable=too-many-public-methods
  _connection: V1Connection
  _project: Project

  @pytest.fixture(autouse=True)
  def setup_project(self, connection, setup):
    del setup
    self._connection = connection
    project_id = random_string(str_length=20).lower()
    self._project = Project(client_id=connection.client_id, reference_id=project_id, name=project_id, created_by=None)
    self.services.database_service.insert(self._project)
    return self._project

  @pytest.fixture
  def experiment(self, connection):
    experiment = Experiment(client_id=connection.client_id)
    self.services.database_service.insert(experiment)
    return experiment

  @pytest.fixture
  def int_values(self):
    return [-10, -2, 0, 2, 10]

  @pytest.fixture
  def id_values(self):
    return list(sorted([random.randint(10000000, 10000000000000) for i in range(5)]))

  @pytest.fixture
  def string_values(self):
    return ["", "a", "b", "abc", "def", "aaaaaaaaaaaaaaaa"]

  @pytest.fixture
  def double_values(self):
    return [0.0, 0.01, 2.02, 10.01, 100.001, 99999]

  def fetch_training_runs(self, project_id=None, **kwargs):
    project_id = project_id or self._project.reference_id
    return self._connection.clients(self._connection.client_id).projects(project_id).training_runs().fetch(**kwargs)

  def insert_training_run(self, **kwargs):
    params = dict(
      client_id=self._connection.client_id,
      project_id=self._project.id,
    )
    extend_dict(params, kwargs)
    self.services.database_service.insert(TrainingRun(**params))

  def create_training_run(self, **kwargs):
    return (
      self._connection.clients(self._connection.client_id)
      .projects(self._project.reference_id)
      .training_runs()
      .create(**kwargs)
    )

  def update_training_run(self, run_id, **kwargs):
    return self._connection.training_runs(run_id).update(**kwargs)

  def test_filter_name_field(self, string_values):
    string_values = compact_sequence(string_values)

    for value in string_values:
      self.create_training_run(name=value)

    for v in string_values:
      assert self.fetch_training_runs(**equals("name", v)).count == 1

    UNUSED_VALUE = "some fake name"
    assert UNUSED_VALUE not in string_values
    assert self.fetch_training_runs(**equals("name", UNUSED_VALUE)).count == 0

  def test_sort_name_field(self, string_values):
    string_values = compact_sequence(string_values)
    random.shuffle(string_values)

    for value in string_values:
      self.create_training_run(name=value)

    ascending_data = self.fetch_training_runs(sort="name", ascending=True).data
    assert [item.name for item in ascending_data] == list(sorted(string_values))
    descending_data = self.fetch_training_runs(sort="name", ascending=False).data
    assert [item.name for item in descending_data] == list(sorted(string_values, reverse=True))

  def test_filter_state_field(self):
    states = []
    for value in ["active"] + ["completed"] + ["failed"] * 2:
      self.create_training_run(name="run", state=value)
      states.append(value)

    for value in ["completed", "failed"]:
      run = self.create_training_run(name="run")
      self.update_training_run(run.id, state=value)
      states.append(value)

    for state in ["active", "completed", "failed"]:
      assert self.fetch_training_runs(**equals("state", state)).count == len([s for s in states if s == state])

  def test_bad_state_filter_value(self):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(**equals("state", "not a real state"))

  @pytest.mark.parametrize("operator", [less_than, less_than_or_equal])
  def test_bad_state_filter_operator(self, operator):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(**operator("state", "active"))

  def test_bad_state_filter_isnull(self):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(**is_null("state"))

  def test_sort_state_field(self, string_values):
    states = ["active"] + ["completed"] * 2 + ["failed"] * 3
    for value in states:
      self.create_training_run(name="run", state=value)

    ascending_data = self.fetch_training_runs(sort="state", ascending=True).data
    assert [item.state for item in ascending_data] == list(sorted(states))
    descending_data = self.fetch_training_runs(sort="state", ascending=False).data
    assert [item.state for item in descending_data] == list(sorted(states, reverse=True))

  @pytest.mark.parametrize("field,db_name,Model", ID_FIELDS)
  def test_filter_id_field(self, id_values, field, db_name, Model):
    for value in id_values:
      if Model is not TrainingRun:
        self.services.database_service.insert(Model(id=value))
      self.insert_training_run(**{db_name: value})

    for i, v in enumerate(id_values):
      assert self.fetch_training_runs(**equals(field, v)).count == 1
      assert self.fetch_training_runs(**equals(field, str(v))).count == 1
      resp = self.fetch_training_runs(**less_than_or_equal(field, v))
      assert resp.count == i + 1
      assert self.fetch_training_runs(**less_than(field, v)).count == i
      assert self.fetch_training_runs(**is_null(field)).count == 0

    UNUSED_VALUE = 1
    assert UNUSED_VALUE not in id_values
    assert self.fetch_training_runs(**equals(field, UNUSED_VALUE)).count == 0

  @pytest.mark.parametrize("field,db_name,Model", ID_FIELDS)
  def test_sort_id_field(self, id_values, field, db_name, Model):
    random.shuffle(id_values)
    for value in id_values:
      if Model is not TrainingRun:
        self.services.database_service.insert(Model(id=value))
      self.insert_training_run(**{db_name: value})

    id_values = list(str(x) for x in sorted(id_values))
    ascending_data = self.fetch_training_runs(sort=field, ascending=True).data
    assert [get_json_key(item, field) for item in ascending_data] == id_values
    descending_data = self.fetch_training_runs(sort=field, ascending=False).data
    assert [get_json_key(item, field) for item in descending_data] == list(reversed(id_values))

  def test_constant_client_id_fields(self, id_values):
    for _ in id_values:
      self.insert_training_run()

    # By definition the client ID must be the same for every value in the list,
    # but we still want to handle them sanely
    count = len(id_values)
    assert self.fetch_training_runs(**equals("client", self._connection.client_id)).count == count
    assert self.fetch_training_runs(**less_than_or_equal("client", self._connection.client_id)).count == count
    assert self.fetch_training_runs(**less_than("client", self._connection.client_id)).count == 0
    assert (
      self.fetch_training_runs(sort="client", ascending=True).data
      == self.fetch_training_runs(sort="id", ascending=True).data
    )

  @pytest.mark.parametrize("field", STRING_FIELDS)
  def test_filter_string_field(self, string_values, field):
    for value in string_values:
      self.create_training_run(name="run", **set_string_clause(field, value))

    for v in string_values:
      assert self.fetch_training_runs(**equals(field, v)).count == 1

    UNUSED_VALUE = "lmn"
    assert UNUSED_VALUE not in string_values
    assert self.fetch_training_runs(**equals(field, UNUSED_VALUE)).count == 0
    assert self.fetch_training_runs(**is_null(field)).count == 0

  @pytest.mark.parametrize("field", STRING_FIELDS)
  def test_sort_string_field(self, string_values, field):
    random.shuffle(string_values)
    for value in string_values:
      self.create_training_run(name="run", **set_string_clause(field, value))

    ascending_data = self.fetch_training_runs(sort=field, ascending=True).data
    assert [get_json_key(item, field) for item in ascending_data] == list(sorted(string_values))
    descending_data = self.fetch_training_runs(sort=field, ascending=False).data
    assert [get_json_key(item, field) for item in descending_data] == list(sorted(string_values, reverse=True))

  @pytest.mark.parametrize("field", NUMERIC_FIELDS)
  def test_filter_numeric_field(self, double_values, field):
    for value in double_values:
      self.create_training_run(name="run", **set_string_clause(field, value))

    for v in double_values:
      assert self.fetch_training_runs(**equals(field, v)).count == 1

    UNUSED_VALUE = -99999.1
    assert UNUSED_VALUE not in double_values
    assert self.fetch_training_runs(**equals(field, UNUSED_VALUE)).count == 0
    assert self.fetch_training_runs(**is_null(field)).count == 0

  @pytest.mark.parametrize("field", NUMERIC_FIELDS)
  def test_sort_numeric_field(self, double_values, field):
    random.shuffle(double_values)
    for value in double_values:
      self.create_training_run(name="run", **set_string_clause(field, value))

    ascending_data = self.fetch_training_runs(sort=field, ascending=True).data
    assert [get_json_key(item, field) for item in ascending_data] == list(sorted(double_values))
    descending_data = self.fetch_training_runs(sort=field, ascending=False).data
    assert [get_json_key(item, field) for item in descending_data] == list(sorted(double_values, reverse=True))

  @pytest.mark.parametrize("field", DATE_FIELDS)
  def test_filter_date_field(self, int_values, field):
    for value in int_values:
      self.insert_training_run(**{field: seconds_to_datetime(value)})

    for i, v in enumerate(int_values):
      assert self.fetch_training_runs(**equals(field, v)).count == 1
      assert self.fetch_training_runs(**less_than_or_equal(field, v)).count == i + 1
      assert self.fetch_training_runs(**less_than(field, v)).count == i

    UNUSED_VALUE = 1
    assert UNUSED_VALUE not in int_values
    assert self.fetch_training_runs(**equals(field, UNUSED_VALUE)).count == 0
    assert self.fetch_training_runs(**is_null(field)).count == 0

  @pytest.mark.parametrize("field", DATE_FIELDS)
  def test_sort_date_field(self, int_values, field):
    random.shuffle(int_values)
    for value in int_values:
      self.insert_training_run(**{field: seconds_to_datetime(value)})

    ascending_data = self.fetch_training_runs(sort=field, ascending=True).data
    assert [get_json_key(item, field) for item in ascending_data] == list(sorted(int_values))
    descending_data = self.fetch_training_runs(sort=field, ascending=False).data
    assert [get_json_key(item, field) for item in descending_data] == list(sorted(int_values, reverse=True))

  def test_filter_deleted_field(self):
    self.insert_training_run(deleted=True)
    self.insert_training_run(deleted=True)
    self.insert_training_run(deleted=False)

    assert self.fetch_training_runs().count == 3
    assert self.fetch_training_runs(**equals("deleted", True)).count == 2
    assert self.fetch_training_runs(**equals("deleted", False)).count == 1

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(**less_than("deleted", False))

  def test_filter_null_field(self):
    self.create_training_run(name="test filter null", **set_string_clause("model.type", "xgboost"))
    self.create_training_run(name="test filter null")

    assert self.fetch_training_runs(**is_null("model.type")).count == 1
    assert self.fetch_training_runs(**is_null("name")).count == 0

  def test_invalid_sort_key(self):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(sort="some.fake.field")

  @pytest.mark.parametrize(
    "field_name,invalid_value",
    [
      ("values.accuracy.value", {}),
      ("values.accuracy.value", True),
      ("values.accuracy.value", ""),
      ("values.accuracy.value", "."),
      ("values.accuracy.value", "0.0"),
      ("values.accuracy.value", "abc"),
      ("values.accuracy.value_stddev", {}),
      ("values.accuracy.value_stddev", True),
      ("values.accuracy.value_stddev", ""),
      ("values.accuracy.value_stddev", "."),
      ("values.accuracy.value_stddev", "0.0"),
      ("values.accuracy.value_stddev", "abc"),
      ("id", True),
      ("id", {}),
      ("id", ""),
      ("id", "."),
      ("id", "abc"),
      ("id", 0.9),
      ("created", True),
      ("created", {}),
      ("created", ""),
      ("created", "."),
      ("created", 0.9),
      ("created", "abc"),
      ("created", "1"),
      ("deleted", {}),
      ("deleted", "abc"),
      ("deleted", "1"),
      ("deleted", 1),
      ("state", {}),
      ("state", True),
      ("state", 1),
      ("state", "invalid-state"),
    ],
  )
  def test_invalid_filter_value(self, field_name, invalid_value):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.fetch_training_runs(**equals(field_name, invalid_value))

  @pytest.mark.parametrize(
    "field",
    [
      "created",
      "deleted",
      "experiment",
      "metadata.double_key",
      "metadata.string_key",
      "name",
      "state",
    ],
  )
  def test_pagination(self, experiment, field):
    count = 5
    for _ in range(count):
      self.insert_training_run(
        created=current_datetime(),
        deleted=random.choice([True, False]),
        experiment_id=experiment.id,
        training_run_data=TrainingRunData(
          name=random_string(),
          metadata=dict_to_protobuf_struct(
            {
              "double_key": random.uniform(0, 1),
              "string_key": random_string(),
            }
          ),
          state=random.choice([TrainingRunData.COMPLETED, TrainingRunData.FAILED, TrainingRunData.ACTIVE]),
        ),
      )
    assert self.fetch_training_runs(limit=1, sort=field).count == count
    assert self.fetch_training_runs(limit=100, sort=field).count == count
    assert self.fetch_training_runs(limit=1, sort=field).paging.before is not None
    assert self.fetch_training_runs(limit=100, sort=field).paging.before is None
    for limit in (1, 2, 3, 100):
      assert len(list(self.fetch_training_runs(limit=limit, sort=field).iterate_pages())) == count

  @pytest.mark.parametrize("limit", (0, 1, 5, 9))
  def test_pagination_nulls(self, experiment, limit):
    count = 10
    for i in range(count):
      self.insert_training_run(training_run_data=TrainingRunData(values_map={"acc": TrainingRunValue(value=i)}))
    for _ in range(count):
      self.insert_training_run(training_run_data=TrainingRunData(values_map={}))

    sort = "values.acc.value"
    pagination = self.fetch_training_runs(limit=limit, sort=sort)
    assert len(pagination.data) == limit
    assert pagination.paging.before
    pagination = self.fetch_training_runs(limit=count, sort=sort, before=pagination.paging.before)
    assert len(pagination.data) == count - limit
    assert not pagination.paging.before

    pagination = self.fetch_training_runs(limit=limit, sort=sort, ascending="true")
    assert len(pagination.data) == limit
    assert pagination.paging.after
    pagination = self.fetch_training_runs(limit=count, sort=sort, after=pagination.paging.after)
    assert len(pagination.data) == count - limit
    assert not pagination.paging.after

  def test_search(self):
    count = 10
    keyword = "one ring"
    for _ in range(count):
      prefix, suffix = random_string(5), random_string(5)
      for name in (f"{prefix} {keyword}", f"{prefix} {keyword} {suffix}", f"{keyword} {suffix}", f"{prefix} {suffix}"):
        self.insert_training_run(
          created=current_datetime(),
          deleted=random.choice([True, False]),
          training_run_data=TrainingRunData(
            name=name,
            state=random.choice([TrainingRunData.COMPLETED, TrainingRunData.FAILED, TrainingRunData.ACTIVE]),
          ),
        )

    assert self.fetch_training_runs(limit=100, search=keyword).count == count * 3  # 3 / 4 cases should match

  @pytest.fixture(scope="function")
  def project_for_testing_count(self):
    project_id = random_string(str_length=20).lower()
    project = Project(client_id=self._connection.client_id, reference_id=project_id, name=project_id, created_by=None)
    self.services.database_service.insert(project)
    return project

  def check_defined_fields(self, defined_fields, expected_fields, num_of_training_runs):
    for field in defined_fields:
      if field.key in expected_fields:
        assert field.count == num_of_training_runs
      else:
        assert field.count == 0

  def do_primitive_fields_test(self, project, db_field_name, api_field_name, values):
    kwargs = {"project_id": project.id}
    for value in values:
      kwargs[db_field_name] = value
      self.insert_training_run(**kwargs)

    training_runs = self.fetch_training_runs(project_id=project.reference_id)
    if api_field_name in {"observation", "completed"}:
      supplemental_defined_fields = {api_field_name, "finished"}
    else:
      supplemental_defined_fields = {api_field_name}
    expected_fields = INVARIABLY_DEFINED_FIELDS.union(supplemental_defined_fields)
    self.check_defined_fields(training_runs.defined_fields, expected_fields, len(values))

  @pytest.mark.parametrize(
    "api_field_name, db_field_name, Model",
    TRAINING_RUN_TESTABLE_PRIMITIVE_ID_FIELDS,
  )
  def test_primitive_id_fields_count(self, api_field_name, db_field_name, Model, project_for_testing_count):
    project = project_for_testing_count

    values = []
    for _ in range(TEST_VALUES_COUNT):
      m = Model()
      self.services.database_service.insert(m)
      values.append(m.id)
    if Model is UnprocessedSuggestion:
      for suggestion_id in values:
        self.services.database_service.insert(ProcessedSuggestion(suggestion_id=suggestion_id))

    self.do_primitive_fields_test(project, db_field_name, api_field_name, values)

  @pytest.mark.parametrize(
    "api_field_name, db_field_name, values",
    TRAINING_RUN_TESTABLE_PRIMITIVE_VALUE_FIELDS,
  )
  def test_primitive_fields_count(self, api_field_name, db_field_name, values, project_for_testing_count):
    project = project_for_testing_count

    self.do_primitive_fields_test(project, db_field_name, api_field_name, values)

  @pytest.mark.parametrize(
    "api_field_name, db_field_name, values",
    TRAINING_RUN_TESTABLE_PROTOBUF_FIELDS_WITH_VALUES,
  )
  def test_protobuf_fields_count(self, api_field_name, db_field_name, values, project_for_testing_count):
    project = project_for_testing_count
    training_run_params = {}
    for value in values:
      training_run_params[db_field_name] = value
      self.insert_training_run(project_id=project.id, training_run_data=TrainingRunData(**training_run_params))

    training_runs = self.fetch_training_runs(project_id=project.reference_id)
    expected_fields = INVARIABLY_DEFINED_FIELDS.union({api_field_name})
    self.check_defined_fields(training_runs.defined_fields, expected_fields, len(values))
