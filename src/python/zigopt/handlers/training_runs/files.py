# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.file.model import MAX_NAME_LENGTH, File
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import FileJsonBuilder
from zigopt.net.errors import BadParamError, NotFoundError
from zigopt.protobuf.gen.file.filedata_pb2 import FileData
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import TrainingRun
from zigopt.user.model import User


training_run_files_json_name = TrainingRunData.DESCRIPTOR.fields_by_name["files"].json_name


class FileCreateHandler(Handler):
  PARAM_NAME = "name"
  PARAM_FILENAME = "filename"
  PARAM_CONTENT_LENGTH = "content_length"
  PARAM_CONTENT_TYPE = "content_type"
  PARAM_CONTENT_MD5 = "content_md5"
  REQUIRED_INPUT_PARAMS = [
    (PARAM_CONTENT_LENGTH, ValidationType.positive_integer),
    (PARAM_CONTENT_TYPE, ValidationType.mime_type),
    (PARAM_CONTENT_MD5, ValidationType.md5),
  ]
  OPTIONAL_INPUT_PARAMS = [
    (PARAM_NAME, ValidationType.string),
    (PARAM_FILENAME, ValidationType.string),
  ]

  def prepare(self):
    if not self.services.file_service.enabled:
      raise NotFoundError()
    super().prepare()

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_client(
      self.services, WRITE, objects["client"]
    )

  def parse_params(self, request):
    provided_params = request.params()
    acceptable_params = [key for key, _ in self.REQUIRED_INPUT_PARAMS + self.OPTIONAL_INPUT_PARAMS]
    unaccepted_params = provided_params.keys() - acceptable_params
    if unaccepted_params:
      raise BadParamError(
        f"Unknown parameters: {unaccepted_params}. Only the following parameters are accepted: {acceptable_params}"
      )
    params = {}
    for key, validator in self.REQUIRED_INPUT_PARAMS:
      params[key] = get_with_validation(provided_params, key, validator)
    for key, validator in self.OPTIONAL_INPUT_PARAMS:
      params[key] = get_opt_with_validation(provided_params, key, validator)
      if params[key] and len(params[key]) > MAX_NAME_LENGTH:
        raise BadParamError(f"{key} must be less than {MAX_NAME_LENGTH} characters long.")
    if not (params.get(self.PARAM_NAME) or params.get(self.PARAM_FILENAME)):
      raise BadParamError("At least one of ('name', 'filename') is required.")
    return params

  def create_file_and_json_builder(self, params, auth, client, created_by):
    file_data = FileData(
      content_length=params[self.PARAM_CONTENT_LENGTH],
      content_type=params[self.PARAM_CONTENT_TYPE],
      content_md5=params[self.PARAM_CONTENT_MD5],
    )
    file_obj = File(
      name=params[self.PARAM_NAME],
      filename=params[self.PARAM_FILENAME],
      data=file_data,
      client_id=client.id,
      created_by=created_by,
    )
    file_obj, upload_info = self.services.file_service.insert_file_and_create_upload_data(file_obj)
    return file_obj, FileJsonBuilder(
      file_obj=file_obj,
      upload_info=upload_info,
    )


class TrainingRunsCreateFileHandler(TrainingRunHandler, FileCreateHandler):
  """Attaches a file to the training run.
    Files can be images or documents, they are intended to be useful for displaying information about your training
    run so you can better understand the outcome of the results. There is a per-organization limit on accumulated file
    size.
    ---
    tags:
      - "training runs"
    parameters:
      - $ref: "#/components/parameters/TrainingRunId"
    requestBody:
        content:
          application/json:
            schema:
               $ref: '#/components/schemas/TrainingRunFilePost'
    responses:
      200:
        description: "Training Run updated."
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TrainingRunFile'
      204:
        description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                      returned instead of 200, without any data."
      401:
        description: "Unauthorized. Authorization was incorrect."
      400:
        description: "Bad Request Format. Failed validation of some kind."
      404:
        description: "Not found. No experiment is at that URI."
      429:
        description: "Client has engaged too many events recently and is rate limited."
      5XX:
        description: "Unexpected Error"
    components:
      schemas:
        TrainingRunFileBase:
          type: object
          properties:
            content_length:
              type: integer
              minimum: 0
              description: "The length, in bytes, of the file."
            content_type:
              type: string
              maxLength: 100
              description: "MIME type for the file upload. Must be valid MIME type."
            content_md5:
              type: string
              maxLength: 16
              description: "base64 encoded MD5 hash string of the file upload, to confirm the upload is successful."
            filename:
              type: string
              maxLength: 100
              description: "Name of file. One of filename and name must be present."
            name:
              type: string
              maxLength: 100
              description: "Name of file. One of filename and name must be present."
        TrainingRunFilePost:
          required: ["content_length", "content_type", "content_md5"]
          allOf:
            - $ref: "#/components/schemas/TrainingRunFileBase"
        TrainingRunFile:
          allOf:
            - $ref: "#/components/schemas/TrainingRunBase"
            - type: object
              properties:
                client:
                  type: integer
                  minimum: 1
                  description: "The id of the client that this file is associated with. The same as in the larger
                                training_run."
                user:
                  type: integer
                  minimum: 1
                  description: "The id of the user that created this file."
                created:
                  type: integer
                  minimum: 0
                  description: "The epoch timestamp of when the server created this file upload."
                download:
                  type: object
                  properties:
                    url:
                      type: string
                      description: "The url to download the file from."
                upload:
                  type: object
                  properties:
                    url:
                      type: string
                      description: "The URL to upload the file to."
                    method:
                      type: string
                      description: "The method to upload the data with, e.g. PUT or POST."
                    headers:
                      type: object
                      description: "Map where the key is header names, and the values are the header values, for the
                                    upload of data."
    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self, params):
    assert self.auth is not None
    current_user: User | None = self.auth.current_user

    file_obj, file_json_builder = self.create_file_and_json_builder(
      params, self.auth, self.client, napply(current_user, lambda u: u.id)
    )

    update_clause = {
      TrainingRun.training_run_data: self.create_update_clause(
        merge_objects=True,
        training_run_data_json={
          training_run_files_json_name: {file_obj.id: True},
        },
      ),
    }

    self.emit_update(update_clause)

    return file_json_builder
