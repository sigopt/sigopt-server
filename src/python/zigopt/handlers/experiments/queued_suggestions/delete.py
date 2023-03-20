# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.queued_suggestions.base import QueuedSuggestionHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class QueuedSuggestionsDeleteHandler(QueuedSuggestionHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    self.services.queued_suggestion_service.delete_by_id(self.experiment.id, self.queued_suggestion.id)
    return {}
