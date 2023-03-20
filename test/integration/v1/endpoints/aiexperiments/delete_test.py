# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.training_run.model import TrainingRun

from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.experiments_test_base import AiExperimentsTestBase


class TestDeleteAiExperiments(AiExperimentsTestBase, TrainingRunTestMixin):
  @pytest.fixture
  def ai_experiment(self, connection, project):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  @pytest.fixture
  def deleted_ai_experiment(self, connection, project, services):
    e = connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    db_e = services.experiment_service.find_by_id(e.id)
    services.experiment_service.delete(db_e)
    return connection.aiexperiments(e.id).fetch()

  @pytest.fixture
  def ai_experiment_with_runs(self, connection, project, services):
    e = connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    runs = [
      TrainingRun(
        experiment_id=e.id,
        client_id=e.client,
        deleted=False,
      )
      for _ in range(10)
    ]
    services.database_service.insert_all(runs)
    e = connection.aiexperiments(e.id).fetch()
    assert e.progress.total_run_count > 0
    return e

  def test_delete(self, connection, ai_experiment):
    e = ai_experiment
    assert e.state == "active"
    connection.aiexperiments(e.id).delete()
    assert connection.aiexperiments(e.id).fetch().state == "deleted"

  def test_idempotent_delete(self, connection, deleted_ai_experiment):
    e = deleted_ai_experiment
    connection.aiexperiments(e.id).delete()
    assert connection.aiexperiments(e.id).fetch().state == "deleted"

  def test_delete_without_runs(self, services, connection, ai_experiment_with_runs):
    e = ai_experiment_with_runs
    connection.aiexperiments(e.id).delete()
    assert (
      services.database_service.count(
        services.database_service.query(TrainingRun)
        .filter(TrainingRun.experiment_id == int(e.id))
        .filter(~TrainingRun.deleted)
      )
      == e.progress.total_run_count
    )
    assert (
      services.database_service.count(
        services.database_service.query(TrainingRun)
        .filter(TrainingRun.experiment_id == int(e.id))
        .filter(TrainingRun.deleted)
      )
      == 0
    )

  def test_delete_with_runs(self, services, connection, ai_experiment_with_runs):
    e = ai_experiment_with_runs
    connection.aiexperiments(e.id).delete(include_runs=True)
    assert (
      services.database_service.count(
        services.database_service.query(TrainingRun)
        .filter(TrainingRun.experiment_id == int(e.id))
        .filter(~TrainingRun.deleted)
      )
      == 0
    )
    assert (
      services.database_service.count(
        services.database_service.query(TrainingRun)
        .filter(TrainingRun.experiment_id == int(e.id))
        .filter(TrainingRun.deleted)
      )
      == e.progress.total_run_count
    )
