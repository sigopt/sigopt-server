# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH, Project

from integration.v1.test_base import V1Base


class TestProjectExperimentList(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, services, client_id):
    return services.project_service.insert(
      Project(
        name="test project for experiment list",
        reference_id=random_string(MAX_ID_LENGTH).lower(),
        client_id=client_id,
        created_by=None,
      )
    )

  @pytest.fixture
  def another_project(self, services, client_id):
    return services.project_service.insert(
      Project(
        name="another test project for experiment list",
        reference_id=random_string(MAX_ID_LENGTH).lower(),
        client_id=client_id,
        created_by=None,
      )
    )

  def test_list_single(self, connection, client_id, project):
    e = connection.create_any_experiment(project=project.reference_id)
    page = connection.clients(client_id).projects(project.reference_id).experiments().fetch()
    assert page.count == 1
    assert len(page.data) == 1
    assert page.data[0].id == e.id
    assert page.data[0].project == project.reference_id

  def test_list_excludes_other_projects(
    self,
    connection,
    client_id,
    project,
    another_project,
  ):
    e = connection.create_any_experiment(project=project.reference_id)
    connection.create_any_experiment()
    connection.create_any_experiment(project=another_project.reference_id)
    page = connection.clients(client_id).projects(project.reference_id).experiments().fetch()
    assert page.count == 1
    assert len(page.data) == 1
    assert page.data[0].id == e.id
    assert page.data[0].project == project.reference_id

  def test_list_multiple_pages(
    self,
    connection,
    client_id,
    project,
  ):
    number_of_experiments = 10
    experiments = [connection.create_any_experiment(project=project.reference_id) for _ in range(number_of_experiments)]
    page = connection.clients(client_id).projects(project.reference_id).experiments().fetch(limit=2)
    assert page.count == 10
    assert len(page.data) == 2
    all_fetched_experiments = list(
      connection.clients(client_id)
      .projects(project.reference_id)
      .experiments()
      .fetch(limit=2, sort="id", ascending=False)
      .iterate_pages()
    )
    experiments_by_descending_id = reversed(experiments)
    assert [e.id for e in all_fetched_experiments] == [e.id for e in experiments_by_descending_id]
    assert all(e.project == project.reference_id for e in all_fetched_experiments)
