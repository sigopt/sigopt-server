# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.project.model import Project
from zigopt.project.service import ProjectExistsException

from integration.service.project.test_base import ProjectServiceTestBase


class TestProjectServiceInsert(ProjectServiceTestBase):
  def test_insert_project_same_client(self, project_service, client):
    project1_reference_id = "testproject-1"
    project2_reference_id = "testproject-2"

    project1 = Project(name="test project", reference_id=project1_reference_id, client_id=client.id, created_by=None)
    inserted_project1 = project_service.insert(project1)
    assert inserted_project1.reference_id == project1_reference_id

    project2 = Project(name="test project 2", reference_id=project1_reference_id, client_id=client.id, created_by=None)
    with pytest.raises(ProjectExistsException):
      project_service.insert(project2)
    project2.reference_id = project2_reference_id
    inserted_project2 = project_service.insert(project2)
    assert inserted_project2.reference_id == project2_reference_id

  def test_insert_project_multiple_clients(self, project_service, client, another_client):
    reference_id = "testproject"
    inserted_project1 = project_service.insert(
      Project(
        name="test project",
        reference_id=reference_id,
        client_id=client.id,
        created_by=None,
      )
    )
    assert inserted_project1.reference_id == reference_id
    inserted_project2 = project_service.insert(
      Project(
        name="test project 2",
        reference_id=reference_id,
        client_id=another_client.id,
        created_by=None,
      )
    )
    assert inserted_project2.reference_id == reference_id
