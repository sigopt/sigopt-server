# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.handlers.validate.suggestion import validate_suggestion_json_dict_for_create
from zigopt.json.builder import SuggestionJsonBuilder
from zigopt.net.errors import ForbiddenError
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta, SuggestionMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.suggestion.from_json import build_suggestion_data_from_json
from zigopt.suggestion.unprocessed.model import SuggestionMetaProxy

from libsigopt.aux.errors import SigoptValidationError


class SuggestionsCreateHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return request.params()

  def handle(self, json_dict):
    assert self.auth is not None
    assert self.experiment is not None

    if self.experiment.deleted:
      raise SigoptValidationError(f"Cannot create suggestions for deleted experiment {self.experiment.id}")

    if self.experiment.runs_only:
      raise ForbiddenError(
        f"Suggestions cannot be created directly for experiment {self.experiment.id}, please create runs instead"
      )

    processed_suggestion_meta = SuggestionsCreateHandler.make_processed_suggestion_meta_from_json(json_dict)
    validate_suggestion_json_dict_for_create(json_dict, self.experiment)

    if "assignments" in json_dict or "task" in json_dict:
      suggestion = self.services.suggestion_broker.explicit_suggestion(
        experiment=self.experiment,
        suggestion_meta=self.make_suggestion_meta_from_json(json_dict),
        processed_suggestion_meta=processed_suggestion_meta,
      )
    else:
      suggestion = self.services.suggestion_broker.serve_suggestion(
        experiment=self.experiment, processed_suggestion_meta=processed_suggestion_meta, auth=self.auth
      )

    return SuggestionJsonBuilder(self.experiment, suggestion, self.auth)

  def make_suggestion_meta_from_json(self, json_dict):
    return SuggestionMetaProxy(
      (SuggestionMeta(suggestion_data=build_suggestion_data_from_json(self.experiment, json_dict)))
    )

  @staticmethod
  def make_processed_suggestion_meta_from_json(json_dict):
    suggestion_meta = ProcessedSuggestionMeta()

    client_provided_data = BaseExperimentsCreateHandler.get_client_provided_data(json_dict)
    if client_provided_data is not None:
      suggestion_meta.client_provided_data = client_provided_data

    return suggestion_meta
