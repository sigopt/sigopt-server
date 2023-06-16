# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.json.builder import TrainingRunJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class TrainingRunsDeleteHandler(TrainingRunHandler):
  """Remove a training run.
    This process removes a training run via a soft delete, it will still be retrievable with specific search
    tuned to look for soft deletes. It will automatically handle updating the checkpoint count with this one
    deleted.
    ---
    tags:
      - "training runs"
    parameters:
      - $ref: "#/components/parameters/TrainingRunId"
    responses:
      200:
        description: "Training run deleted."
        content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrainingRun'
      401:
        description: "Unauthorized. Authorization was incorrect."
      404:
        description: "Not found. No training_run is at that URI."
      429:
        description: "Client has engaged too many events recently and is rate limited."
      5XX:
        description: "Unexpected Error"
    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    assert self.training_run is not None
    assert self.project is not None

    self.services.training_run_service.set_deleted(self.training_run.id)
    self.training_run.deleted = True
    checkpoint_count = self.services.checkpoint_service.count_by_training_run(self.training_run.id)

    return TrainingRunJsonBuilder(
      self.training_run,
      checkpoint_count=checkpoint_count,
      project=self.project,
    )
