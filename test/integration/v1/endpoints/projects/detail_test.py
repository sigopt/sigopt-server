# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.project.model import Project

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestProjectsDetail(V1Base):
  TEST_PROJECT_NAME = "Test experiment project"
  TEST_PROJECT_REFERENCE_ID = "test-project"

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, services, client_id):
    return services.project_service.insert(
      Project(
        name=self.TEST_PROJECT_NAME,
        reference_id=self.TEST_PROJECT_REFERENCE_ID,
        client_id=client_id,
        created_by=None,
      )
    )

  def test_invalid_client(self, services, connection):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients("0").projects("not-a-project").fetch()

  def test_invalid_project(self, services, connection, client_id):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(client_id).projects("not-a-project").fetch()

  def test_fetch_project(self, services, connection, client_id, project):
    fetched_project = connection.clients(client_id).projects(project.reference_id).fetch()
    assert fetched_project.name == project.name
    assert fetched_project.id == project.reference_id
    assert fetched_project.client == str(project.client_id)
