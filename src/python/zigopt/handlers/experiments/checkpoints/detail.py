# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.checkpoint.model import Checkpoint
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.json.builder import CheckpointJsonBuilder, PaginationJsonBuilder
from zigopt.net.errors import NotFoundError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class CheckpointsDetailHandler(TrainingRunHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def __init__(self, services, request, *, training_run_id, checkpoint_id, experiment_id=None):
    super().__init__(services, request, experiment_id=experiment_id, training_run_id=training_run_id)
    self._checkpoint_id = checkpoint_id

  def handle(self):
    checkpoint = self.services.checkpoint_service.find_by_id(self._checkpoint_id)
    if checkpoint.training_run_id != self.training_run.id:
      raise NotFoundError(f"No checkpoint with id {self._checkpoint_id} found for training run {self.training_run.id}")
    return CheckpointJsonBuilder(checkpoint, self.experiment)


class CheckpointsDetailMultiHandler(TrainingRunHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def parse_params(self, request):
    return request

  def handle(self, request):
    paging = request.get_paging()
    ascending = request.optional_bool_param("ascending") or False
    query = self.services.database_service.query(Checkpoint).filter(Checkpoint.training_run_id == self.training_run_id)
    checkpoint_count = self.services.database_service.count(query)
    checkpoints, new_before, new_after = self.services.query_pager.fetch_page(
      query,
      Checkpoint.id,
      paging=paging,
      ascending=ascending,
    )

    return PaginationJsonBuilder(
      data=[CheckpointJsonBuilder(checkpoint, self.experiment) for checkpoint in checkpoints],
      count=checkpoint_count,
      before=new_before,
      after=new_after,
    )
