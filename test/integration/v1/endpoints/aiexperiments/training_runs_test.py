# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import AiExperimentsTestBase


TEST_CREATE_FIELDS = [
  ("assignments", None),
  ("assignments", {"unoptimized": 1}),
  ("assignments", {}),
  ("deleted", None),
  ("dev_metadata", None),
  ("dev_metadata", {"x": 1}),
  ("dev_metadata", {}),
  ("favorite", False),
  ("favorite", None),
  ("favorite", True),
  ("logs", None),
  ("logs", {"stdout": {"content": "123"}}),
  ("logs", {}),
  ("metadata", None),
  ("metadata", {"x": 1}),
  ("metadata", {}),
  ("model", None),
  ("model", {}),
  ("model", {"type": "xgboost"}),
  ("source_code", None),
  ("source_code", {"content": "123"}),
  ("source_code", {"hash": "123"}),
  ("state", "active"),
  ("state", "completed"),
  ("state", "failed"),
  ("values", None),
  ("values", {"unoptimized": {"value": 1, "value_stddev": 1}}),
  ("values", {"unoptimized": {"value": 1}}),
  ("values", {DEFAULT_AI_EXPERIMENT_META["metrics"][0]["name"]: {"value": 1, "value_stddev": 1}}),
  ("values", {DEFAULT_AI_EXPERIMENT_META["metrics"][0]["name"]: {"value": 1}}),
  ("values", {}),
]

PAIRWISE_TEST_CREATE_CASES = []


def create_pairwise_cases():
  for field1, value1 in TEST_CREATE_FIELDS:
    for field2, value2 in TEST_CREATE_FIELDS:
      if field1 < field2:
        PAIRWISE_TEST_CREATE_CASES.append((field1, value1, field2, value2))


create_pairwise_cases()


class TestAiExperimentTrainingRuns(AiExperimentsTestBase):
  @pytest.fixture
  def ai_experiment(self, connection, project):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  def _recursively_check(self, data, expected):
    if expected is None:
      return
    if isinstance(expected, list):
      assert isinstance(data, list)
      assert len(data) == len(expected)
      for v1, v2 in zip(data, expected):
        self._recursively_check(v1, v2)
      return
    if isinstance(expected, dict):
      assert isinstance(data, dict)
      for k, v in expected.items():
        self._recursively_check(data.get(k), v)
      return
    assert data == expected

  def check_field(self, connection, ai_experiment, training_run, field, expected_value):
    for run in (
      training_run,
      connection.training_runs(training_run.id).fetch(),
    ):
      data = copy.deepcopy(run.to_json()[field])
      self._recursively_check(data, expected_value)

  @pytest.mark.parametrize(
    "field,value",
    [
      ("assignments", "1"),
      ("assignments", 1),
      ("assignments", []),
      ("completed", 0),
      ("deleted", 1),
      ("deleted", "1"),
      ("deleted", []),
      ("deleted", {}),
      ("dev_metadata", "1"),
      ("dev_metadata", 1),
      ("dev_metadata", []),
      ("favorite", "1"),
      ("favorite", 1),
      ("favorite", []),
      ("favorite", {}),
      ("finished", True),
      ("logs", []),
      ("logs", {"l": {}}),
      ("logs", {"l": {"unknown": ""}}),
      ("metadata", "1"),
      ("metadata", []),
      ("metadata", []),
      ("model", "1"),
      ("model", 1),
      ("model", []),
      ("observation", "1"),
      ("project", None),
      ("state", "1"),
      ("state", 1),
      ("state", []),
      ("state", {}),
      ("suggestion", "1"),
      ("sys_metadata", "1"),
      ("sys_metadata", 1),
      ("sys_metadata", []),
      ("unknown", "1"),
      ("unknown", 1),
      ("unknown", None),
      ("unknown", []),
      ("unknown", {}),
      ("updated", 0),
      ("user", "1"),
      ("values", "1"),
      ("values", 1),
      ("values", []),
      ("values", [{"name": "m1"}]),
    ],
  )
  def test_create_bad_param(self, connection, ai_experiment, field, value):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.aiexperiments(ai_experiment.id).training_runs().create(name="test run", **{field: value})

  def test_create_run(self, connection, ai_experiment):
    run = connection.aiexperiments(ai_experiment.id).training_runs().create(name="test run")
    data = run.to_json()
    assert {"name", "state", "deleted", "observation", "suggestion"} <= set(data)

  @pytest.mark.parametrize("field,value", TEST_CREATE_FIELDS)
  def test_create_run_single_field(self, connection, ai_experiment, field, value):
    run = connection.aiexperiments(ai_experiment.id).training_runs().create(name="test run", **{field: value})
    self.check_field(connection, ai_experiment, run, field, value)

  @pytest.mark.parametrize("field1,value1,field2,value2", PAIRWISE_TEST_CREATE_CASES)
  def test_create_run_multiple_fields(self, connection, ai_experiment, field1, value1, field2, value2):
    run = (
      connection.aiexperiments(ai_experiment.id)
      .training_runs()
      .create(name="test run", **{field1: value1, field2: value2})
    )
    self.check_field(connection, ai_experiment, run, field1, value1)
    self.check_field(connection, ai_experiment, run, field2, value2)

  def test_create_populates_assignments(self, connection, ai_experiment):
    training_run = connection.aiexperiments(ai_experiment.id).training_runs().create(name="test run")
    run_assignments = training_run.to_json()["assignments"]
    assert all(p.name in run_assignments for p in ai_experiment.parameters)
    assert isinstance(run_assignments["a"], int)
    assert isinstance(run_assignments["b"], (int, float))
    assert isinstance(run_assignments["c"], str)

  def test_create_with_partial_assignments(self, connection, ai_experiment):
    training_run = (
      connection.aiexperiments(ai_experiment.id).training_runs().create(name="test run", assignments={"a": 1})
    )
    run_assignments = training_run.to_json()["assignments"]
    assert run_assignments["a"] == 1
    assert isinstance(run_assignments["a"], int)
    for v in run_assignments.values():
      assert v is not None

  def test_create_completed_with_partial_assignments(self, connection, ai_experiment):
    training_run = (
      connection.aiexperiments(ai_experiment.id)
      .training_runs()
      .create(name="test run", assignments={"a": 1}, state="completed")
    )
    run_assignments = training_run.to_json()["assignments"]
    assert run_assignments["a"] == 1
    assert isinstance(run_assignments["a"], int)
    for v in run_assignments.values():
      assert v is not None
