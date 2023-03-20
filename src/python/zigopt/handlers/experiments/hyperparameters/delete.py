# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class ExperimentsHyperparametersDeleteHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    self._reset_hyperparameters()
