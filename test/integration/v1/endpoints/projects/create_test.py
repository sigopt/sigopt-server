# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.protobuf.dict import protobuf_struct_to_dict

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestCreateProjects(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  def test_project_create_extra_fields(self, services, connection, client_id):
    project_id = "project-1"
    project_name = "test project create"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).projects().create(
        id=project_id,
        name=project_name,
        this_should_never_be_a_valid_field=True,
      )

  def test_project_create(self, services, connection, client_id):
    project_id = "project-1"
    project_name = "test project create"
    project = (
      connection.clients(client_id)
      .projects()
      .create(
        id=project_id,
        name=project_name,
      )
    )
    assert project.id == project_id
    assert project.client == client_id
    assert project.user == connection.user_id
    assert project.created > 0
    assert project.updated == project.created
    assert project.name == project_name
    assert project.metadata is None
    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=client_id,
      reference_id=project_id,
    )
    assert db_project.reference_id == project_id

  def test_project_create_with_metadata(self, services, connection, client_id):
    project_id = "project-2"
    project_name = "test project create with metadata"
    project_metadata = {"meta_test_key": "meta_test_value"}
    project = (
      connection.clients(client_id)
      .projects()
      .create(
        id=project_id,
        name=project_name,
        metadata=project_metadata,
      )
    )
    assert project.id == project_id
    assert project.client == client_id
    assert project.user == connection.user_id
    assert project.created > 0
    assert project.updated == project.created
    assert project.name == project_name
    assert project.metadata.to_json() == project_metadata
    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=client_id,
      reference_id=project_id,
    )
    assert db_project.reference_id == project_id
    assert protobuf_struct_to_dict(db_project.data.metadata) == project_metadata

  def test_project_create_conflicting(self, connection, client_id):
    project_id = "project-conflicting"
    project_name = "test project create conflicting"
    connection.clients(client_id).projects().create(
      id=project_id,
      name=project_name,
    )
    with RaisesApiException(HTTPStatus.CONFLICT):
      connection.clients(client_id).projects().create(
        id=project_id,
        name=project_name,
      )

  def test_project_create_with_dev_token(self, services, development_connection, client_id):
    project_id = "project-1"
    project_name = "test project create"
    project = (
      development_connection.clients(client_id)
      .projects()
      .create(
        id=project_id,
        name=project_name,
      )
    )
    assert project.id == project_id
    assert project.client == client_id
    assert project.created > 0
    assert project.updated == project.created
    assert project.name == project_name
    assert project.metadata is None
    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=client_id,
      reference_id=project_id,
    )
    assert db_project.reference_id == project_id
