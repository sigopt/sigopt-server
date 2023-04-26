# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus
from typing import Any, Callable

import pytest

from zigopt.common.sigopt_datetime import unix_epoch as get_unix_epoch
from zigopt.experiment.model import Experiment

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import AiExperimentsTestBase


unix_epoch_timestamp = 0
unix_epoch = get_unix_epoch()
TEST_UPDATES: list[tuple[str, Any, Callable[[Experiment], bool]]] = [
  ("budget", 13, lambda e: e.budget == 13),
  ("budget", None, lambda e: e.budget is None),
  ("metadata", None, lambda e: e.metadata is None),
  ("metadata", {"x": 1}, lambda e: e.metadata.to_json() == {"x": 1}),
  ("metadata", {}, lambda e: e.metadata.to_json() == {}),
  ("name", "updated name", lambda e: e.name == "updated name"),
  ("parallel_bandwidth", 3, lambda e: e.parallel_bandwidth == 3),
  ("parallel_bandwidth", None, lambda e: e.parallel_bandwidth is None),
  ("state", "active", lambda e: e.state == "active"),
  ("state", "deleted", lambda e: e.state == "deleted"),
]


class TestUpdateAiExperiments(AiExperimentsTestBase):
  def assert_ai_experiment_updated(self, connection, e, checker):
    assert checker(e) is True
    assert checker(connection.aiexperiments(e.id).fetch())

  @pytest.fixture
  def ai_experiment(self, connection, project):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  def test_noop(self, connection, ai_experiment):
    e = connection.aiexperiments(ai_experiment.id).update()
    json1 = ai_experiment.to_json()
    json2 = e.to_json()
    assert unix_epoch_timestamp < json1.pop("updated") <= json2.pop("updated")
    assert json1 == json2

  @pytest.mark.parametrize("field,new_value,checker", TEST_UPDATES)
  def test_single_field(self, connection, ai_experiment, field, new_value, checker):
    e = connection.aiexperiments(ai_experiment.id).update(**{field: new_value})
    self.assert_ai_experiment_updated(connection, e, checker)

  @pytest.mark.parametrize("field1,new_value1,checker1", TEST_UPDATES)
  @pytest.mark.parametrize("field2,new_value2,checker2", TEST_UPDATES)
  def test_multiple_fields(self, connection, ai_experiment, field1, new_value1, checker1, field2, new_value2, checker2):
    if field1 == field2:
      return
    e = connection.aiexperiments(ai_experiment.id).update(**{field1: new_value1, field2: new_value2})
    self.assert_ai_experiment_updated(connection, e, checker1)
    self.assert_ai_experiment_updated(connection, e, checker2)

  @pytest.mark.parametrize("field1,new_value1,checker1", TEST_UPDATES)
  @pytest.mark.parametrize("field2,new_value2,checker2", TEST_UPDATES)
  def test_sequential_updates(
    self, connection, ai_experiment, field1, new_value1, checker1, field2, new_value2, checker2
  ):
    e = connection.aiexperiments(ai_experiment.id).update(**{field1: new_value1})
    self.assert_ai_experiment_updated(connection, e, checker1)
    e = connection.aiexperiments(ai_experiment.id).update(**{field2: new_value2})
    self.assert_ai_experiment_updated(connection, e, checker2)
    if field1 != field2:
      self.assert_ai_experiment_updated(connection, e, checker1)

  @pytest.mark.parametrize("new_project", [None, "non-existent-project"])
  def test_cannot_update_project(self, connection, ai_experiment, new_project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.aiexperiments(ai_experiment.id).update(project=new_project)

  def test_update_changes_time(self, services, connection, ai_experiment):
    e = ai_experiment
    services.database_service.update(
      services.database_service.query(Experiment).filter(Experiment.id == int(e.id)),
      {Experiment.date_updated: unix_epoch},
    )
    assert connection.aiexperiments(e.id).fetch().updated == unix_epoch_timestamp
    updated_e = connection.aiexperiments(e.id).update()
    assert updated_e.updated > unix_epoch_timestamp
    fetched_e = connection.aiexperiments(e.id).fetch()
    assert fetched_e.updated > unix_epoch_timestamp
    assert updated_e.updated == fetched_e.updated
