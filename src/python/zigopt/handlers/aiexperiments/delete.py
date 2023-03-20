# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.aiexperiments.base import AiExperimentHandler
from zigopt.handlers.experiments.delete import ExperimentsDeleteHandler


class AiExperimentsDeleteHandler(AiExperimentHandler, ExperimentsDeleteHandler):
  """Delete a single AiExperiment
    This deletes an AiExperiment. It can also delete all runs from the AiExperiment as well, if desired. All deletes are
    soft deletes, just mean that they will by default be filtered out of visualizations. All can be viewed and
    revived at any time.
    ---
      tags:
        - "aiexperiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AiExperimentDelete"
      responses:
        200:
          description: "AiExperiment deleted."
        401:
          description: "Unauthorized. Authorization was incorrect."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        404:
          description: "Not found. No AiExperiment is at that URI."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        schemas:
          AiExperimentDelete:
            type: object
            properties:
              include_runs:
                type: boolean
                default: "false"
                description: "If true, all the runs for this AiExperiment will be marked as deleted as well."

    """
