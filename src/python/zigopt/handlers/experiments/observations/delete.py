# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.observations.base import ObservationHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class ObservationsDeleteHandler(ObservationHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return request.optional_bool_param("no_optimize")

  def handle(self, no_optimize):
    num_observations = self.services.observation_service.count_by_experiment(self.experiment)
    self.services.observation_service.set_delete(self.experiment, self.observation.id)
    num_observations -= 1

    if no_optimize is not True:
      self.services.observation_service.optimize(
        experiment=self.experiment,
        num_observations=num_observations,
      )

    return {}


class ObservationsDeleteAllHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    self.services.observation_service.delete_all_for_experiment(self.experiment)
    self.services.aux_service.reset_hyperparameters(self.experiment)
    return {}
