# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.v1.test_base import V1Base


class TestClientsProjectsNotesList(V1Base):
  @pytest.fixture
  def project(self, connection):
    project_id = "notes_create_test_project"
    return connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)

  def test_returns_empty_if_none(self, connection, project):
    notes = connection.clients(connection.client_id).projects(project.id).notes().fetch()

    assert notes.count == 0
    assert not notes.data

  def test_returns_most_recent_if_any(self, connection, project):
    note1 = connection.clients(connection.client_id).projects(project.id).notes().create(contents="Note 1")
    note2 = connection.clients(connection.client_id).projects(project.id).notes().create(contents="Note 2")

    notes = connection.clients(connection.client_id).projects(project.id).notes().fetch()

    assert notes.count == 1
    assert note1 not in notes.data
    assert note2 in notes.data
