# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.handlers.experiments.suggestions.base import SuggestionHandler
from zigopt.json.builder import SuggestionJsonBuilder
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class SuggestionsUpdateHandler(SuggestionHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return request.params()

  def handle(self, json_dict):
    suggestion_meta = ProcessedSuggestionMeta()
    client_provided_data = BaseExperimentsCreateHandler.get_client_provided_data(
      json_dict, default=self.suggestion.client_provided_data
    )
    # pylint: disable=protobuf-undefined-attribute
    suggestion_meta.SetFieldIfNotNone("client_provided_data", client_provided_data)
    # pylint: enable=protobuf-undefined-attribute

    processed = self.suggestion.processed
    processed.processed_suggestion_meta = suggestion_meta
    self.services.processed_suggestion_service.upsert_suggestion(processed)
    return SuggestionJsonBuilder(self.experiment, self.suggestion, self.auth)
