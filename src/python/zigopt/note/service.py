# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Mapping

from sqlalchemy.orm import Query

from zigopt.client.model import Client
from zigopt.note.model import Note, ProjectNote
from zigopt.project.model import Project
from zigopt.services.base import Service


class NoteService(Service):
  fkeys = {
    ProjectNote: [
      ("client", ProjectNote.project_client_id),
      ("project", ProjectNote.project_project_id),
    ],
  }

  def _build_base_read_query(self, NoteCls: type[Note], resource_id_map: Mapping[str, Any]) -> Query:
    query = self.services.database_service.query(NoteCls)
    for parent_resource, fkey in self.fkeys[NoteCls]:
      query = query.filter(fkey == resource_id_map[parent_resource])
    return query

  def find_project_notes_by_client_and_project(self, client: Client, project: Project) -> Query:
    resource_id_map = {"client": client.id, "project": project.id}
    return self._build_base_read_query(ProjectNote, resource_id_map)

  def insert(self, note: Note) -> None:
    self.services.database_service.insert(note)
