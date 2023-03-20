# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.handlers.experiments.suggestions.create import SuggestionsCreateHandler
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.queued_suggestion.queued_suggestion_meta_pb2 import QueuedSuggestionMeta
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta
from zigopt.queued_suggestion.model import QueuedSuggestion
from zigopt.suggestion.lib import SuggestionAlreadyProcessedError

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestProcess(UnprocessedSuggestionServiceTestBase):
  @pytest.fixture(params=[True, False])
  def unprocessed_suggestion(self, request, services, experiment):
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    if request.param:
      services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed_suggestion])
    return unprocessed_suggestion

  @pytest.fixture(params=[True, False])
  def conditional_unprocessed_suggestion(self, request, services, conditional_experiment):
    unprocessed_suggestion = self.new_conditional_unprocessed_suggestion(conditional_experiment)
    if request.param:
      services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed_suggestion])
    return unprocessed_suggestion

  @pytest.fixture(params=[dict(), dict(metadata=None), dict(metadata=dict(foo="bar", baz=25))])
  def processed_suggestion_meta(self, request):
    return SuggestionsCreateHandler.make_processed_suggestion_meta_from_json(request.param)

  def test_process(self, services, experiment, unprocessed_suggestion, processed_suggestion_meta):
    suggestion = services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=processed_suggestion_meta,
    )
    assert suggestion.id == unprocessed_suggestion.id
    assert suggestion.experiment_id == experiment.id
    assert suggestion.get_assignments(experiment) == dict(p1=0)
    assert suggestion.source == unprocessed_suggestion.source
    assert suggestion.client_provided_data == processed_suggestion_meta.GetFieldOrNone("client_provided_data")
    assert suggestion.state == "open"
    assert suggestion.processed.queued_id is None

  def test_cannot_process_twice(self, services, experiment, unprocessed_suggestion, processed_suggestion_meta):
    services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=processed_suggestion_meta,
    )

    with pytest.raises(SuggestionAlreadyProcessedError):
      services.unprocessed_suggestion_service.process(
        experiment=experiment,
        unprocessed_suggestion=unprocessed_suggestion,
        processed_suggestion_meta=processed_suggestion_meta,
      )

  def test_can_find_processed_suggestion(self, services, experiment, unprocessed_suggestion, processed_suggestion_meta):
    assert services.suggestion_service.find_by_id(unprocessed_suggestion.id) is None

    services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=processed_suggestion_meta,
    )

    suggestion = services.suggestion_service.find_by_id(unprocessed_suggestion.id)
    assert suggestion.id == unprocessed_suggestion.id
    assert suggestion.experiment_id == experiment.id
    assert suggestion.get_assignments(experiment) == dict(p1=0)
    assert suggestion.source == unprocessed_suggestion.source
    assert suggestion.client_provided_data == processed_suggestion_meta.GetFieldOrNone("client_provided_data")
    assert suggestion.state == "open"
    assert suggestion.processed.queued_id is None

  def test_process_with_queued_id(self, services, experiment, unprocessed_suggestion):
    queued = QueuedSuggestion(
      experiment_id=experiment.id,
      meta=QueuedSuggestionMeta(),
    )
    services.queued_suggestion_service.insert(queued)
    assert services.queued_suggestion_service.find_by_id(experiment.id, queued.id) is not None

    suggestion = services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=ProcessedSuggestionMeta(),
      queued_id=queued.id,
    )

    assert services.queued_suggestion_service.find_by_id(experiment.id, queued.id) is None

    assert suggestion.id == unprocessed_suggestion.id
    assert suggestion.experiment_id == experiment.id
    assert suggestion.get_assignments(experiment) == dict(p1=0)
    assert suggestion.source == unprocessed_suggestion.source
    assert suggestion.client_provided_data is None
    assert suggestion.state == "open"
    assert suggestion.processed.queued_id == queued.id

  def test_process_with_conditionals(self, services, conditional_experiment, conditional_unprocessed_suggestion):
    suggestion = services.unprocessed_suggestion_service.process(
      experiment=conditional_experiment,
      unprocessed_suggestion=conditional_unprocessed_suggestion,
      processed_suggestion_meta=ProcessedSuggestionMeta(),
    )

    assert suggestion.id == conditional_unprocessed_suggestion.id
    assert suggestion.experiment_id == conditional_experiment.id
    assert suggestion.get_assignments(conditional_experiment) == dict(p1=0, c1=1)
    assert suggestion.source == conditional_unprocessed_suggestion.source
    assert suggestion.client_provided_data is None
    assert suggestion.state == "open"
    assert suggestion.processed.queued_id is None
