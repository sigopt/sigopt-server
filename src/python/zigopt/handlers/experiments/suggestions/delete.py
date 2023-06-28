# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.suggestions.base import SuggestionHandler
from zigopt.handlers.validate.suggestion import validate_state
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class SuggestionsDeleteHandler(SuggestionHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    assert self.experiment is not None
    assert self.suggestion is not None

    self.services.processed_suggestion_service.set_delete_by_ids(self.experiment, [self.suggestion.id])
    return {}


class SuggestionsDeleteAllHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return validate_state(request.optional_param("state"))

  def handle(self, state):
    assert self.experiment is not None

    if state is None:
      self.services.processed_suggestion_service.delete_all_for_experiment(self.experiment)
    else:
      self.services.processed_suggestion_service.delete_open_for_experiment(self.experiment)

    return {}
