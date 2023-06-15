# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.net.errors import UnprocessableEntityError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class MetricImportancesUpdateHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    assert self.experiment is not None

    num_observations = self.services.observation_service.count_by_experiment(self.experiment)
    q_msg = self.services.optimize_queue_service.always_enqueue_importances(
      experiment=self.experiment,
      num_observations=num_observations,
    )
    if q_msg is None:
      raise UnprocessableEntityError(
        "Parameter importances update failed. (This experiment may not support importances.)"
      )
    self.services.queue_monitor.robust_enqueue([q_msg], self.experiment)
