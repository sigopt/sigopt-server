# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.json.builder import ProjectJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ, TokenMeta


class ClientsProjectsDetailHandler(ProjectHandler):
  """Return individual project
    This returns a specific project by id.
    ---
        tags:
            - "projects"
        parameters:
          - $ref: "#/components/parameters/ClientId"
          - $ref: "#/components/parameters/ProjectReferenceId"
        responses:
          200:
            description: "Project returned."
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Project'
          401:
            description: "Unauthorized. Authorization was incorrect."
          400:
            description: "Bad Request Format. Failed validation of some kind."
          404:
            description: "Not found. No project is at that URI."
          429:
            description: "Client has engaged too many events recently and is rate limited."
          5XX:
            description: "Unexpected Error"
    """

  authenticator = api_token_authentication
  required_permissions = READ
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SHARED_EXPERIMENT_SCOPE)

  def handle(self):
    assert self.project is not None

    return ProjectJsonBuilder(
      self.project,
      experiment_count=self.services.experiment_service.count_by_project(self.project.client_id, self.project.id),
      training_run_count=self.services.training_run_service.count_by_project(self.project.client_id, self.project.id),
    )
