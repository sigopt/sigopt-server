# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from datetime import timedelta

import pytest

from zigopt.common.sigopt_datetime import datetime_to_seconds, unix_epoch
from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment
from zigopt.project.model import MAX_ID_LENGTH, Project

from integration.v1.test_base import V1Base


create_time = unix_epoch()
update_time = create_time + timedelta(seconds=1)


class TestProjectDateUpdated(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, services, client_id):
    project = Project(
      name="project for date_updated tests",
      reference_id=random_string(MAX_ID_LENGTH).lower(),
      client_id=client_id,
      created_by=None,
      date_created=create_time,
      date_updated=create_time,
    )
    services.project_service.insert(project)
    return project

  def refresh_project(self, services, project):
    return self.services.project_service.find_by_client_and_id(
      client_id=project.client_id,
      project_id=project.id,
    )

  def reset_date_updated(self, services, project, experiment):
    services.database_service.update(
      services.project_service.find_by_client_and_ids_query(
        client_id=project.client_id,
        project_ids=[project.id],
      ),
      {Project.date_updated: create_time},
    )
    services.database_service.update(
      services.database_service.query(Experiment).filter(Experiment.id == experiment.id),
      {Experiment.date_updated: create_time},
    )
    project = self.refresh_project(services, project)
    assert project.date_updated == create_time
    return project

  def test_experiment_create_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
      assert datetime_to_seconds(project.date_updated) == e.updated

  def test_add_experiment_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment() as e:
      assert e.project is None
      self.reset_date_updated(services, project, e)
      updated_e = connection.experiments(e.id).update(project=project.reference_id)
      assert updated_e.project == project.reference_id
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
      assert datetime_to_seconds(project.date_updated) == updated_e.updated

  def test_remove_experiment_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      self.reset_date_updated(services, project, e)
      updated_e = connection.experiments(e.id).update(project=None)
      assert updated_e.project is None
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
      assert datetime_to_seconds(project.date_updated) == updated_e.updated

  def test_experiment_archive_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      self.reset_date_updated(services, project, e)
      connection.experiments(e.id).delete()
      assert e.project == project.reference_id
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time

  @pytest.mark.skip(reason="suggestions dont actually update experiments")
  def test_create_suggestion_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      self.reset_date_updated(services, project, e)
      suggestion = connection.experiments(e.id).suggestions().create()
      project = self.refresh_project(services, project)
      assert datetime_to_seconds(project.date_updated) == suggestion.created

  def test_create_observation_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      suggestion = connection.experiments(e.id).suggestions().create()
      self.reset_date_updated(services, project, e)
      observation = (
        connection.experiments(e.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          values=[{"value": 0}],
        )
      )
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
      assert datetime_to_seconds(project.date_updated) == observation.created

  def test_observation_update_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      suggestion = connection.experiments(e.id).suggestions().create()
      observation = (
        connection.experiments(e.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          values=[{"value": 0}],
        )
      )
      self.reset_date_updated(services, project, e)
      observation = (
        connection.experiments(e.id)
        .observations(observation.id)
        .update(
          values=[{"value": 1}],
        )
      )
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
      experiment = connection.experiments(e.id).fetch()
      assert datetime_to_seconds(project.date_updated) == experiment.updated

  def test_observation_delete_updates_project(self, services, connection, client_id, project):
    assert project.date_updated == create_time
    with connection.create_any_experiment(project=project.reference_id) as e:
      assert e.project == project.reference_id
      suggestion = connection.experiments(e.id).suggestions().create()
      observation = (
        connection.experiments(e.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          values=[{"value": 0}],
        )
      )
      self.reset_date_updated(services, project, e)
      connection.experiments(e.id).observations(observation.id).delete()
      project = self.refresh_project(services, project)
      assert project.date_updated >= update_time
