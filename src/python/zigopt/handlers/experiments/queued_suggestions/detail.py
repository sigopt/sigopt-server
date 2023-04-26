# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.queued_suggestions.base import QueuedSuggestionHandler
from zigopt.json.builder import PaginationJsonBuilder, QueuedSuggestionJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.queued_suggestion.model import QueuedSuggestion


class QueuedSuggestionsDetailHandler(QueuedSuggestionHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    return QueuedSuggestionJsonBuilder.json(self.experiment, self.queued_suggestion)


class QueuedSuggestionsDetailMultiHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def parse_params(self, request):
    return request.get_paging()

  def handle(self, paging):
    assert self.experiment is not None

    query = self.services.queued_suggestion_service.query_by_experiment_id(self.experiment.id)
    count = self.services.database_service.count(query)
    queued_suggestions, new_before, new_after = self.services.query_pager.fetch_page(
      query,
      QueuedSuggestion.id,
      paging=paging,
    )

    return PaginationJsonBuilder(
      data=[
        QueuedSuggestionJsonBuilder(self.experiment, queued_suggestion) for queued_suggestion in queued_suggestions
      ],
      count=count,
      before=new_before,
      after=new_after,
    )
