# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.validate.metadata import validate_metadata
from zigopt.handlers.validate.project import validate_project_json_dict_for_create
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import ProjectJsonBuilder
from zigopt.net.errors import ConflictingDataError
from zigopt.project.model import Project
from zigopt.project.service import ProjectExistsException
from zigopt.protobuf.gen.project.projectdata_pb2 import ProjectData
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


# pylint: disable=anomalous-backslash-in-string
class ClientsProjectsCreateHandler(ClientHandler):
  """Create a new project for the current client.
    This creates a new project (a group of experiments focused on answering a single research question) for a specific
    client.
    ---
    tags:
      - "projects"
    requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ProjectPost"
    parameters:
      - $ref: "#/components/parameters/ClientId"
    responses:
      201:
        description: "New Project created."
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Project'
      204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 201."
      401:
        description: "Unauthorized. Authorization was incorrect."
      400:
        description: "Bad Request Format. Failed validation of some kind."
      429:
        description: "Client has engaged too many events recently and is rate limited."
      5XX:
        description: "Unexpected Error"
    components:
      tags:
        - name: projects
          descriptions: Operations involving projects as a first class object.
      schemas:
        Project:
          type: object
          allOf:
            - $ref: '#/components/schemas/ProjectBase'
            - type: object
              properties:
                client:
                  type: integer
                  description: "ID of the client this project is associated with."
                user:
                  type: integer
                  description: "ID of the user who created this project."
                created:
                  type: integer
                  description: "Epoch time of creation of this project."
                updated:
                  type: integer
                  description: "Epoch time that this project was last updated."
                experiment_count:
                  type: integer
                  description: "Number of experiments associated with this project."
                training_run_count:
                  type: integer
                  description: "Number of training runs, combined, in all experiments associated with this project
                                plus any that might be directly associated to this project and not any experiment."
                deleted:
                  type: boolean
                  description: "If true this project is soft-deleted, else project is active."
        ProjectPost:
          type: object
          allOf:
            - $ref: '#/components/schemas/ProjectBase'
        ProjectBase:
          type: object
          required: [name, id]
          properties:
            name:
              type: string
              description: "The human friendly name of the project."
              minLength: 1
              maxLength: 100
            id:
              type: string
              minLength: 1
              maxLength: 32
              pattern: ^[a-z0-9\-_\.]+$                                                      # noqa: W605
              description: "Computer friendly name of the project. A string that uniquely (across the entire client)
                            identifies this project. Must consist of URL-friendly characters (lowercase letters,
                            numbers, -, _, .)."
            metadata:
              type: object
              description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                            strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                            client side."
    """

  authenticator = api_token_authentication
  required_permissions = WRITE
  allow_development = True

  Params = ImmutableStruct(
    "Params",
    [
      "name",
      "reference_id",
      "metadata",
    ],
  )

  def parse_params(self, request):
    data = request.params()
    validate_project_json_dict_for_create(data)
    return self.Params(
      name=get_with_validation(data, "name", ValidationType.string),
      reference_id=get_with_validation(data, "id", ValidationType.id_string),
      metadata=napply(get_opt_with_validation(data, "metadata", ValidationType.metadata), validate_metadata),
    )

  def handle(self, params):  # type: ignore
    assert self.auth is not None
    assert self.client is not None

    project_name = params.name
    project_reference_id = params.reference_id
    project = Project(
      name=project_name,
      reference_id=project_reference_id,
      client_id=self.client.id,
      data=ProjectData(metadata=params.metadata),
      created_by=(self.auth.current_user and self.auth.current_user.id),
    )
    try:
      inserted_project = self.services.project_service.insert(project)
    except ProjectExistsException as e:
      raise ConflictingDataError(f"The experiment project with id `{e.reference_id}` already exists.") from e
    return ProjectJsonBuilder(inserted_project, experiment_count=0, training_run_count=0)
