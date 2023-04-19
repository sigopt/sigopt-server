# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.json.builder import TagJsonBuilder
from zigopt.net.errors import NotFoundError, UnprocessableEntityError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ, WRITE
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import TrainingRun

from libsigopt.aux.errors import SigoptValidationError


training_run_tags_json_name = TrainingRunData.DESCRIPTOR.fields_by_name["tags"].json_name


class BaseTrainingRunsTagHandler(TrainingRunHandler):
  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    if not super().can_act_on_objects(requested_permission, objects):
      return False
    client = objects["client"]
    return self.auth.can_act_on_client(self.services, READ, client)


class TrainingRunsAddTagHandler(BaseTrainingRunsTagHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  ID_PARAM = "id"

  INPUT_PARAMS = [
    (ID_PARAM, ValidationType.id),
  ]

  def parse_params(self, request):
    provided_params = request.params()
    acceptable_params = [key for key, _ in self.INPUT_PARAMS]
    unaccepted_params = provided_params.keys() - acceptable_params
    if unaccepted_params:
      raise SigoptValidationError(
        f"Unknown parameters: {unaccepted_params}. Only the following parameters are accepted: {acceptable_params}"
      )
    params = {}
    for key, validator in self.INPUT_PARAMS:
      params[key] = get_with_validation(provided_params, key, validator)
    return params

  def handle(self, params):
    assert self.training_run is not None

    tag_id = params[self.ID_PARAM]
    tag = self.services.tag_service.find_by_client_and_id(
      client_id=self.training_run.client_id,
      tag_id=tag_id,
    )

    if tag is None:
      raise UnprocessableEntityError(
        f"The tag with id {tag_id} cannot be added to this training run because it does not exist."
      )

    update_clause = {
      TrainingRun.training_run_data: self.create_update_clause(
        merge_objects=True,
        training_run_data_json={
          training_run_tags_json_name: {tag_id: True},
        },
      ),
    }

    self.emit_update(update_clause)

    return TagJsonBuilder(tag=tag)


class TrainingRunsRemoveTagHandler(BaseTrainingRunsTagHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def __init__(self, *args, tag_id, **kwargs):
    super().__init__(*args, **kwargs)
    if tag_id is None:
      raise Exception("Tag id is required")
    self.tag_id = tag_id
    self.tag = None

  def find_objects(self):
    objs = super().find_objects()
    tag = self.services.tag_service.find_by_client_and_id(
      client_id=objs["training_run"].client_id,
      tag_id=self.tag_id,
    )
    if tag is None:
      raise NotFoundError("Tag not found")
    objs["tag"] = tag
    return objs

  def can_act_on_objects(self, requested_permission, objects):
    if not super().can_act_on_objects(requested_permission, objects):
      return False
    tag = objects["tag"]
    if tag.client_id is None:
      return False
    client = objects["client"]
    assert client.id == tag.client_id
    return True

  def parse_params(self, request):
    return None

  def handle(self, params):
    assert self.tag is not None

    update_clause = {
      TrainingRun.training_run_data: self.create_update_clause(
        merge_objects=True,
        training_run_data_json={
          training_run_tags_json_name: {self.tag_id: None},
        },
      ),
    }

    self.emit_update(update_clause)

    return TagJsonBuilder(tag=self.tag)
