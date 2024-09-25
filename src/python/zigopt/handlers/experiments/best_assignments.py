# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import BestAssignmentsJsonBuilder, PaginationJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ExperimentsBestAssignmentsHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  Params = ImmutableStruct(
    "Params",
    ("path",),
  )

  def parse_params(self, request):
    return self.Params(path=request.path)

  def best_observations(self):
    assert self.experiment is not None

    return self.services.experiment_best_observation_service.get_best_observations(
      self.experiment,
      self.services.observation_service.all_data(self.experiment),
    )

  def handle(self, params):  # type: ignore
    assert self.experiment is not None

    best_observations = self.best_observations()
    return PaginationJsonBuilder(data=[BestAssignmentsJsonBuilder(self.experiment, b) for b in best_observations])
