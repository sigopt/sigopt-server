# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.validate.note import validate_note_json_dict
from zigopt.json.builder import ProjectNoteJsonBuilder
from zigopt.note.model import ProjectNote
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class ClientsProjectsNotesCreateHandler(ProjectHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct("Params", ["contents"])

  def parse_params(self, request):
    data = request.params()
    validate_note_json_dict(data)
    return self.Params(contents=data.get("contents"))

  def handle(self, params):
    note = ProjectNote(
      contents=params.contents,
      created_by=self.auth.current_user.id,
      project_client_id=self.client.id,
      project_project_id=self.project.id,
    )
    self.services.note_service.insert(note)

    return ProjectNoteJsonBuilder(note, self.project)
