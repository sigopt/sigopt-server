# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.handlers.validate.note import note_schema

from integration.base import RaisesApiException
from integration.enhanced_info_objects import ProjectNote
from integration.v1.test_base import V1Base


class TestClientsProjectsNotesCreate(V1Base):
  @pytest.fixture
  def project(self, connection):
    project_id = "notes_create_test_project"
    return connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)

  def test_basic_create(self, connection, project):
    now = unix_timestamp()

    contents = "Ayo boi wassup"
    note = connection.clients(connection.client_id).projects(project.id).notes().create(contents=contents)

    assert isinstance(note, ProjectNote)
    assert note.client == connection.client_id
    assert note.contents == contents
    assert note.created >= now
    assert note.project == project.id
    assert note.user == connection.user_id

  def test_error_if_contents_missing(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).notes().create()

  def test_error_if_invalid_contents(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).notes().create(contents=123)

  def test_error_if_contents_too_large(self, connection, project):
    contents = "a" * (note_schema["properties"]["contents"]["maxLength"] + 1)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).notes().create(contents=contents)

  def test_error_if_additional_properties_provided(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).notes().create(additional="property")
