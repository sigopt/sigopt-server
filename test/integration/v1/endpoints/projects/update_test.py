# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus
from time import sleep

import pytest

from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH, MAX_NAME_LENGTH, Project
from zigopt.protobuf.dict import dict_to_protobuf_struct, protobuf_struct_to_dict
from zigopt.protobuf.lib import copy_protobuf

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestProjectsUpdateEndpoint(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, services, client_id):
    return services.project_service.insert(
      Project(
        name="project update endpoint test",
        reference_id=random_string(MAX_ID_LENGTH).lower(),
        client_id=client_id,
        created_by=None,
      )
    )

  def test_project_not_found(self, connection, client_id):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(client_id).projects("project-doesnt-exist").update(name="should fail")

  @pytest.mark.parametrize(
    "key,value",
    [
      ("client", "1"),
      ("created", 0),
      ("updated", 0),
      ("field_should_be_invalid", True),
    ],
  )
  def test_update_invalid(self, key, value, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(project.client_id).projects(project.reference_id).update(**{key: value})

  def test_update_name(self, services, connection, project):
    new_name = random_string()
    for _ in range(2):
      updated_project = (
        connection.clients(project.client_id)
        .projects(project.reference_id)
        .update(
          name=new_name,
        )
      )
      assert updated_project.id == project.reference_id
      assert updated_project.client == str(project.client_id)
      assert updated_project.name == new_name
      assert updated_project.metadata is None

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.name == new_name
    assert db_project.data.HasField("metadata") is False

  @pytest.mark.parametrize(
    "new_name",
    [
      None,
      "",
      "X" * (MAX_NAME_LENGTH + 1),
    ],
  )
  def test_update_invalid_name(self, new_name, services, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(project.client_id).projects(project.reference_id).update(
        name=new_name,
      )

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.name == project.name

  def test_update_metadata(self, services, connection, project):
    new_metadata = {"test_key": random_string()}
    for _ in range(2):
      updated_project = (
        connection.clients(project.client_id)
        .projects(project.reference_id)
        .update(
          metadata=new_metadata,
        )
      )
      assert updated_project.id == project.reference_id
      assert updated_project.client == str(project.client_id)
      assert updated_project.name == project.name
      assert updated_project.metadata.to_json() == new_metadata

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.name == project.name
    assert protobuf_struct_to_dict(db_project.data.metadata) == new_metadata

  def test_clear_metadata(self, services, connection, project):
    data = copy_protobuf(project.data)
    original_metadata = {"test_key": "test_value"}
    data.metadata.CopyFrom((dict_to_protobuf_struct(original_metadata)))
    services.project_service.update(
      client_id=project.client_id,
      reference_id=project.reference_id,
      data=data,
    )

    updated_project = connection.clients(project.client_id).projects(project.reference_id).update()
    assert updated_project.metadata.to_json() == original_metadata
    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert protobuf_struct_to_dict(db_project.data.metadata) == original_metadata

    for _ in range(2):
      updated_project = (
        connection.clients(project.client_id)
        .projects(project.reference_id)
        .update(
          metadata=None,
        )
      )
      assert updated_project.id == project.reference_id
      assert updated_project.client == str(project.client_id)
      assert updated_project.name == project.name
      assert updated_project.metadata is None

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.data.HasField("metadata") is False

  def test_update_time(self, services, connection, project):
    sleep(1)

    assert project.date_created == project.date_updated
    updated_project = connection.clients(project.client_id).projects(project.reference_id).update()
    assert updated_project.updated > updated_project.created

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.date_updated > project.date_updated
    assert db_project.date_updated > db_project.date_created

  def test_update_all(self, services, connection, project):
    sleep(1)

    new_metadata = {"test_key": random_string()}
    new_name = random_string()
    for _ in range(2):
      updated_project = (
        connection.clients(project.client_id)
        .projects(project.reference_id)
        .update(
          name=new_name,
          metadata=new_metadata,
        )
      )
      assert updated_project.id == project.reference_id
      assert updated_project.client == str(project.client_id)
      assert updated_project.name == new_name
      assert updated_project.metadata.to_json() == new_metadata

    db_project = services.project_service.find_by_client_and_reference_id(
      client_id=project.client_id,
      reference_id=project.reference_id,
    )
    assert db_project.name == new_name
    assert protobuf_struct_to_dict(db_project.data.metadata) == new_metadata
    assert db_project.date_updated > project.date_updated
    assert db_project.date_updated > db_project.date_created

  def test_archive_and_unarchive(self, services, connection, project):
    assert project.deleted is False
    archived_project = connection.clients(project.client_id).projects(project.reference_id).update(deleted=True)
    assert archived_project.to_json()["deleted"] is True
    archived_project = connection.clients(project.client_id).projects(project.reference_id).fetch()
    assert archived_project.to_json()["deleted"] is True
    unarchived_project = connection.clients(project.client_id).projects(project.reference_id).update(deleted=False)
    assert unarchived_project.to_json()["deleted"] is False
    unarchived_project = connection.clients(project.client_id).projects(project.reference_id).fetch()
    assert unarchived_project.to_json()["deleted"] is False
