# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.db.util import DeleteClause
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.suggestions.base import SuggestionHandler
from zigopt.handlers.validate.suggestion import validate_state
from zigopt.json.builder import PaginationJsonBuilder, SuggestionJsonBuilder
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class SuggestionsDetailHandler(SuggestionHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):  # type: ignore
    return SuggestionJsonBuilder.json(self.experiment, self.suggestion, self.auth)


class SuggestionsDetailMultiHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def parse_params(self, request):
    return request

  def handle(self, request):  # type: ignore
    assert self.auth is not None
    assert self.experiment is not None

    state = validate_state(request.optional_param("state"))
    paging = request.get_paging()
    deleted = request.optional_bool_param("deleted")
    ids = request.optional_list_param("id")
    delete_clause = DeleteClause.DELETED if deleted else DeleteClause.NOT_DELETED

    query = (
      self.services.processed_suggestion_service.query_by_experiment(self.experiment.id, include_deleted=delete_clause)
      .join(UnprocessedSuggestion, ProcessedSuggestion.suggestion_id == UnprocessedSuggestion.id)
      .with_entities(ProcessedSuggestion, UnprocessedSuggestion)
    )

    if ids is not None:
      query = query.filter(UnprocessedSuggestion.id.in_(ids))

    if state is not None:
      assert state == "open"
      query = query.outerjoin(Observation).filter(Observation.id.is_(None))

    count = self.services.database_service.count(query)
    suggestions_page, new_before, new_after = self.services.query_pager.fetch_page(
      query,
      UnprocessedSuggestion.id,
      paging=paging,
    )
    suggestions = self.services.suggestion_service.get_suggestions_set_observations(suggestions_page)

    return PaginationJsonBuilder(
      data=[SuggestionJsonBuilder(self.experiment, suggestion, self.auth) for suggestion in suggestions],
      count=count,
      before=new_before,
      after=new_after,
    )
