# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.note.model import ProjectNote
from zigopt.services.base import Service


class NoteService(Service):
  fkeys = {
    ProjectNote: [
      ("client", ProjectNote.project_client_id),
      ("project", ProjectNote.project_project_id),
    ],
  }

  def _build_base_read_query(self, NoteCls, resource_id_map):
    query = self.services.database_service.query(NoteCls)
    for parent_resource, fkey in self.fkeys[NoteCls]:
      query = query.filter(fkey == resource_id_map[parent_resource])
    return query

  def find_project_notes_by_client_and_project(self, client, project):
    resource_id_map = {"client": client.id, "project": project.id}
    return self._build_base_read_query(ProjectNote, resource_id_map)

  def insert(self, note):
    self.services.database_service.insert(note)
