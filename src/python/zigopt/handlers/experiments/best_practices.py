# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import BestPracticesJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ExperimentsBestPracticesHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    errors = list(self.services.best_practices_service.check_experiment(self.experiment))
    return BestPracticesJsonBuilder(violations=errors)
