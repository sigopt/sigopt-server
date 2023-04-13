# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH, Project

from integration.service.test_base import ServiceBase


class ProjectServiceTestBase(ServiceBase):
  def assert_same_projects(self, a_projects, b_projects):
    assert len(a_projects) == len(b_projects)

    def keys_set(projects):
      return set((g.client_id, g.id) for g in projects)

    assert keys_set(a_projects) == keys_set(b_projects)

  @pytest.fixture
  def client(self, services):
    organization = self.make_organization(services, "Experiment projecting Test Organization")
    client = self.make_client(services, "Experiment projecting Test Client", organization)
    return client

  @pytest.fixture
  def another_client(self, services):
    organization = self.make_organization(services, "Experiment projecting Test Organization")
    client = self.make_client(services, "Experiment projecting Test Another Client", organization)
    return client

  @pytest.fixture
  def project_service(self, services):
    return services.project_service

  def make_project(self, client, name="test project", created_by=None, **kwargs):
    reference_id = random_string(MAX_ID_LENGTH).lower()
    project = Project(
      reference_id=reference_id,
      name=name,
      client_id=client.id,
      created_by=created_by,
      **kwargs,
    )
    return project

  @pytest.fixture
  def project(self, services, client):
    project = self.make_project(client)
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def project_for_user1(self, services, client):
    project = self.make_project(client, name="project created by user 1", created_by=1)
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def project_for_user2(self, services, client):
    project = self.make_project(client, name="project created by user 2", created_by=2)
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def another_project(self, services, client):
    project = self.make_project(client, name="another project")
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def project_in_another_client(self, services, another_client):
    project = self.make_project(another_client, name="project in another client")
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def project_for_user1_in_another_client(self, services, another_client):
    project = self.make_project(another_client, name="project created by user 1 in another client", created_by=1)
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def all_test_projects(
    self,
    project,
    project_for_user1,
    project_for_user2,
    another_project,
    project_in_another_client,
    project_for_user1_in_another_client,
  ):
    return [
      project,
      project_for_user1,
      project_for_user2,
      another_project,
      project_in_another_client,
      project_for_user1_in_another_client,
    ]
