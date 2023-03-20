# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.test_base import V1Base


class TestTrainingRunsDelete(V1Base, TrainingRunTestMixin):
  def test_delete(self, connection, project):
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")
    assert training_run.deleted is False
    assert connection.training_runs(training_run.id).delete().deleted is True
    assert connection.training_runs(training_run.id).fetch().deleted is True

  def test_delete_with_dev_token(self, development_connection, project):
    training_run = (
      development_connection.clients(development_connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(name="run")
    )
    assert training_run.deleted is False
    assert development_connection.training_runs(training_run.id).delete().deleted is True
    assert development_connection.training_runs(training_run.id).fetch().deleted is True

  def test_double_delete(self, connection, project):
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")
    connection.training_runs(training_run.id).delete()
    connection.training_runs(training_run.id).delete()
    assert connection.training_runs(training_run.id).fetch().deleted is True

  def test_delete_cascading(self, connection, project, aiexperiment_in_project, services):
    aiexperiment = aiexperiment_in_project
    training_run = connection.aiexperiments(aiexperiment.id).training_runs().create(name="run")
    connection.training_runs(training_run.id).update(state="failed")
    db_training_run = services.training_run_service.find_by_id(int(training_run.id))
    assert training_run.deleted is False
    suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert suggestion
    assert observation

    assert connection.training_runs(training_run.id).delete().deleted is True
    assert connection.training_runs(training_run.id).fetch().deleted is True

    suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert suggestion is None
    assert observation is None

    services.training_run_service.set_deleted(training_run.id, deleted=False)

    assert connection.training_runs(training_run.id).fetch().deleted is False
    suggestion = services.suggestion_service.find_by_id(db_training_run.suggestion_id)
    observation = services.observation_service.find_by_id(db_training_run.observation_id)
    assert suggestion
    assert observation
