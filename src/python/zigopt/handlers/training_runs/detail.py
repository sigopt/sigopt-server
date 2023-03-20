# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.json.builder import TrainingRunJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class TrainingRunsDetailHandler(TrainingRunHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    checkpoint_count = self.services.checkpoint_service.count_by_training_run(self.training_run.id)
    project = self.services.project_service.find_by_client_and_id(
      client_id=self.training_run.client_id,
      project_id=self.training_run.project_id,
    )
    return TrainingRunJsonBuilder(
      self.training_run,
      checkpoint_count=checkpoint_count,
      project=project,
    )
