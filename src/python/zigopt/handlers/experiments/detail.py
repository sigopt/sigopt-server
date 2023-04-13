# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import ExperimentJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ExperimentsDetailHandler(ExperimentHandler):
  """Return a single specific experiment.
    This returns a specific experiment, by id.
    ---
      tags:
            - "experiments"
      parameters:
        - in: path
          name: experiment_id
          required: true
          schema:
            type: integer
            minimum: 1
          description: "The id of the experiment to be returned."
      responses:
        200:
          description: "Experiment returned."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Experiment'
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
    """

  authenticator = api_token_authentication
  required_permissions = READ
  JsonBuilder = ExperimentJsonBuilder
  redirect_ai_experiments = True

  def handle(self):
    assert self.experiment is not None

    progress_map = self.services.experiment_progress_service.progress_for_experiments([self.experiment])
    progress = progress_map.get(self.experiment.id)
    project = self.services.project_service.find_by_client_and_id(
      client_id=self.experiment.client_id,
      project_id=self.experiment.project_id,
    )

    return self.JsonBuilder(
      experiment=self.experiment,
      progress_builder=progress.json_builder(),
      project=project,
      auth=self.auth,
    )
