# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from libsigopt.aux.errors import SigoptValidationError


class ExperimentsDeleteHandler(ExperimentHandler):
  """Delete a single experiment
    This deletes a an experiment. It can also delete all runs from the experiment as well, if desired. All deletes are
    soft deletes, just mean that they will by default be filtered out of visualizations. All can be viewed and
    revived at any time.
    ---
      tags:
        - "experiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExperimentDelete"
      responses:
        200:
          description: "Experiment deleted."
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
          ExperimentDelete:
            type: object
            properties:
              include_runs:
                type: boolean
                default: "false"
                description: "If true, all the runs for this experiment will be marked as deleted as well."

    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  INCLUDE_RUNS_KEY = "include_runs"
  INCLUDE_RUNS_OPTION_FALSE = "false"
  INCLUDE_RUNS_OPTION_TRUE = "true"
  INCLUDE_RUNS_OPTIONS = {
    INCLUDE_RUNS_OPTION_FALSE,
    INCLUDE_RUNS_OPTION_TRUE,
  }

  def parse_params(self, request):
    include_runs_option = request.optional_param(self.INCLUDE_RUNS_KEY) or self.INCLUDE_RUNS_OPTION_FALSE
    include_runs_option = include_runs_option.lower()
    if include_runs_option not in self.INCLUDE_RUNS_OPTIONS:
      raise SigoptValidationError(f"Invalid option for {self.INCLUDE_RUNS_KEY}: {include_runs_option}")
    return {self.INCLUDE_RUNS_KEY: include_runs_option}

  def handle(self, params):
    if not self.experiment:
      return {}
    if params[self.INCLUDE_RUNS_KEY] == self.INCLUDE_RUNS_OPTION_TRUE:
      self.services.training_run_service.delete_runs_in_experiment(self.experiment)
    self.services.experiment_service.delete(self.experiment)
    return {}
