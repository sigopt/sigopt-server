# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.validate.metadata import validate_metadata
from zigopt.handlers.validate.project import validate_project_json_dict_for_update
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import ProjectJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.lib import CopyFrom


class ClientsProjectsUpdateHandler(ProjectHandler):
  """Updates an existing project.
    This takes an already existing project and sets its new values. Only the values
    that need to be changed should be included in this object, not any existing and unchanged fields. Thus,
    any field not mentioned explicitly in this PUT schema can't be changed after the Project object is created.
    This is conceptually more like a RESTful PATCH call, however for historical reasons we use the PUT verb instead.
    ---
    tags:
      - "projects"
    requestBody:
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ProjectPut"
    parameters:
      - in: path
        name: client_id
        required: true
        schema:
          type: integer
          minimum: 1
        description: "The id of the client that this project will be associated with."
      - in: path
        name: project_reference_id
        required: true
        schema:
          type: string
        description: "The project id of the project, as chosen by the creator of the project."
    responses:
      200:
          description: "Project updated."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
      204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 200, without any data."
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
    components:
      schemas:
        ProjectPut:
          type: object
          properties:
            name:
              type: string
              description: "The human friendly name of the project. Replaces the original name of the project."
              minLength: 1
              maxLength: 100
            metadata:
              type: object
              description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                            strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                            client side. If set to none, will clear all existing metadata, otherwise will merge with
                            existing metadata (any key in both, new will win, otherwise will be the full set of new
                            and old)."
            deleted:
              type: boolean
              description: "If true, this project will be soft-deleted and removed from typical queries (can still
                            be recoved by searching for deleted projects). If false project is active, and can be
                            viewed from get-list etc."

    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct(
    "Params",
    (
      "name",
      "metadata",
      "deleted",
    ),
  )

  _NO_METADATA = object()

  def parse_params(self, request):
    data = request.params()
    validate_project_json_dict_for_update(data)
    name = None
    deleted = None
    if "name" in data:
      name = get_with_validation(data, "name", ValidationType.string)
    metadata = self._NO_METADATA
    if "metadata" in data:
      metadata = napply(get_opt_with_validation(data, "metadata", ValidationType.metadata), validate_metadata)
    if "deleted" in data:
      deleted = get_opt_with_validation(data, "deleted", ValidationType.boolean)
    return self.Params(
      name=name,
      metadata=metadata,
      deleted=deleted,
    )

  def handle(self, params):
    assert self.project is not None

    data = None
    if params.metadata is not self._NO_METADATA:
      data = self.project.data.copy_protobuf()
      if params.metadata is None:
        data.ClearField("metadata")
      else:
        CopyFrom(data.metadata, params.metadata)

    self.services.project_service.update(
      client_id=self.client_id,
      reference_id=self.project_reference_id,
      name=params.name,
      data=data,
      deleted=params.deleted,
    )
    project = self.services.project_service.find_by_client_and_reference_id(
      client_id=self.client_id,
      reference_id=self.project_reference_id,
    )
    return ProjectJsonBuilder(
      project,
      experiment_count=self.services.experiment_service.count_by_project(self.project.client_id, self.project.id),
      training_run_count=self.services.training_run_service.count_by_project(self.project.client_id, self.project.id),
    )
