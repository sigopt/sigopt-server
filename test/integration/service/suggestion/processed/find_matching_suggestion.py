# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta

from integration.service.suggestion.processed.test_base import ProcessedSuggestionServiceTestBase


class TestFindMatchingSuggestion(ProcessedSuggestionServiceTestBase):
  def test_empty(self, services, experiment, suggestion):
    assert services.processed_suggestion_service.find_matching_suggestion(experiment, suggestion) is None
    assert services.processed_suggestion_service.find_matching_open_suggestion(experiment, suggestion) is None

  def test_different(self, services, experiment, suggestion):
    unprocessed = self.new_unprocessed_suggestion(
      experiment,
      p1=suggestion.unprocessed.get_assignments(experiment)["p1"] + 1,
    )
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed])
    services.unprocessed_suggestion_service.process(experiment, unprocessed, ProcessedSuggestionMeta())
    assert services.processed_suggestion_service.find_matching_suggestion(experiment, suggestion) is None
    assert services.processed_suggestion_service.find_matching_open_suggestion(experiment, suggestion) is None

  def test_match(self, services, experiment, suggestion):
    unprocessed = self.new_unprocessed_suggestion(
      experiment,
      p1=suggestion.unprocessed.get_assignments(experiment)["p1"],
    )
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed])
    assert services.processed_suggestion_service.find_matching_suggestion(experiment, suggestion) is None
    assert services.processed_suggestion_service.find_matching_open_suggestion(experiment, suggestion) is None
    services.unprocessed_suggestion_service.process(experiment, unprocessed, ProcessedSuggestionMeta())
    assert (
      services.processed_suggestion_service.find_matching_suggestion(experiment, suggestion).suggestion_id
      == unprocessed.id
    )
    assert (
      services.processed_suggestion_service.find_matching_open_suggestion(experiment, suggestion).suggestion_id
      == unprocessed.id
    )

  def test_closed_match(self, services, experiment, suggestion):
    unprocessed = self.new_unprocessed_suggestion(
      experiment,
      p1=suggestion.unprocessed.get_assignments(experiment)["p1"],
    )
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed])
    services.unprocessed_suggestion_service.process(experiment, unprocessed, ProcessedSuggestionMeta())
    services.observation_service.insert_observations(experiment, [Observation(processed_suggestion_id=unprocessed.id)])
    assert (
      services.processed_suggestion_service.find_matching_suggestion(experiment, suggestion).suggestion_id
      == unprocessed.id
    )
    assert services.processed_suggestion_service.find_matching_open_suggestion(experiment, suggestion) is None
