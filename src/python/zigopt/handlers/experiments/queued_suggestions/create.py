# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import QueuedSuggestionJsonBuilder
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.queued_suggestion.queued_suggestion_meta_pb2 import QueuedSuggestionMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.queued_suggestion.model import QueuedSuggestion
from zigopt.suggestion.from_json import build_suggestion_data_from_json


class QueuedSuggestionsCreateHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return request.params()

  def handle(self, json_dict):
    assert self.experiment is not None

    if self.experiment.deleted:
      raise BadParamError(f"Cannot create QueuedSuggestions for deleted experiment {self.experiment.id}")

    queued_suggestion = QueuedSuggestion(
      experiment_id=self.experiment.id,
      meta=QueuedSuggestionMeta(  # pylint: disable=protobuf-type-error
        suggestion_data=build_suggestion_data_from_json(self.experiment, json_dict),
      ),
    )
    self.services.queued_suggestion_service.insert(queued_suggestion)
    return QueuedSuggestionJsonBuilder.json(self.experiment, queued_suggestion)
