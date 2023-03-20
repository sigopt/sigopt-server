# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.aiexperiments.base import AiExperimentHandler
from zigopt.handlers.experiments.detail import ExperimentsDetailHandler


class AiExperimentsDetailHandler(AiExperimentHandler, ExperimentsDetailHandler):
  """Return a single specific AiExperiment.
    This returns a specific AiExperiment, by id.
    ---
      tags:
            - "aiexperiments"
      parameters:
        - in: path
          name: experiment_id
          required: true
          schema:
            type: integer
            minimum: 1
          description: "The id of the AiExperiment to be returned."
      responses:
        200:
          description: "AiExperiment returned."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AiExperiment'
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
