# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.service.project.test_base import ProjectServiceTestBase


class TestProjectServiceFind(ProjectServiceTestBase):
  def test_find_by_client_and_id(self, project_service, all_test_projects):
    for project in all_test_projects:
      found_project = project_service.find_by_client_and_id(client_id=project.client_id, project_id=project.id)
      assert found_project is not None
      assert found_project.id == project.id
      assert found_project.reference_id == project.reference_id
      assert found_project.client_id == project.client_id

  def test_find_by_client_and_reference_id(self, project_service, all_test_projects):
    for project in all_test_projects:
      found_project = project_service.find_by_client_and_reference_id(
        client_id=project.client_id,
        reference_id=project.reference_id,
      )
      assert found_project is not None
      assert found_project.id == project.id
      assert found_project.reference_id == project.reference_id
      assert found_project.client_id == project.client_id

  def test_find_by_client_and_user(
    self,
    project_service,
    client,
    project_for_user1,
    project_for_user2,
    all_test_projects,
  ):
    client_user1_projects = project_service.find_by_client_and_user(client_id=client.id, user_id=1)
    self.assert_same_projects(client_user1_projects, [project_for_user1])

    client_user2_projects = project_service.find_by_client_and_user(client_id=client.id, user_id=2)
    self.assert_same_projects(client_user2_projects, [project_for_user2])

  def test_find_by_client_id(self, project_service, client, another_client, all_test_projects):
    for test_client in (client, another_client):
      client_projects = [project for project in all_test_projects if project.client_id == test_client.id]
      found_client_projects = project_service.find_by_client_id(client_id=test_client.id)
      self.assert_same_projects(found_client_projects, client_projects)

  def test_count_by_client_id(self, project_service, client, another_client, all_test_projects):
    for test_client in (client, another_client):
      client_project_count = sum(project.client_id == test_client.id for project in all_test_projects)
      assert project_service.count_by_client_id(client_id=test_client.id) == client_project_count
