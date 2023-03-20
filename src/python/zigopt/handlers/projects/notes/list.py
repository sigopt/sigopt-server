# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.json.builder.note import ProjectNoteJsonBuilder
from zigopt.json.builder.paging import PaginationJsonBuilder
from zigopt.note.model import ProjectNote
from zigopt.pagination.paging import PagingRequest
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ClientsProjectsNotesListHandler(ProjectHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    query = self.services.note_service.find_project_notes_by_client_and_project(
      self.client,
      self.project,
    )

    # NOTE: gets only the latest note for a given project, for now
    notes, _, _ = self.services.query_pager.fetch_page(
      query,
      ProjectNote.date_created,
      PagingRequest(limit=1, before=None, after=None),
      nulls_descendant=True,
    )

    return PaginationJsonBuilder(
      [ProjectNoteJsonBuilder(note, self.project) for note in notes],
      count=1 if notes else 0,
    )
