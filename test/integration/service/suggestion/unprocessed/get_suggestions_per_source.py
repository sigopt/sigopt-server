# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestGetAllRedisSuggestions(UnprocessedSuggestionServiceTestBase):
  def test_get_suggestions_per_source(self, services, experiment):
    source = UnprocessedSuggestion.Source.SPE
    original_unprocessed_suggestions = [
      self.new_unprocessed_suggestion(experiment, p1=i, source=source) for i in range(5)
    ]
    expected_uuids = set(s.uuid_value for s in original_unprocessed_suggestions)
    services.unprocessed_suggestion_service.insert_unprocessed_suggestions(original_unprocessed_suggestions)

    unprocessed_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    uuids = set(s.uuid_value for s in unprocessed_suggestions)
    assert uuids == expected_uuids

    # with specified source
    unprocessed_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment, [source])
    uuids = set(s.uuid_value for s in unprocessed_suggestions)
    assert uuids == expected_uuids

    # confirm other source is empty
    source2 = UnprocessedSuggestion.Source.GP_CATEGORICAL
    unprocessed_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment, [source2])
    uuids = set(s.uuid_value for s in unprocessed_suggestions)
    assert uuids == set()

  def test_get_suggestions_per_source_ignores_invalid(self, services, experiment):
    source = UnprocessedSuggestion.Source.SPE
    valid_unprocessed_suggestions = [self.new_unprocessed_suggestion(experiment, p1=i, source=source) for i in range(5)]
    invalid_unprocessed_suggestions = [
      self.new_unprocessed_suggestion(experiment, p1=i, source=source) for i in (-11, 11)
    ]
    all_suggestions = valid_unprocessed_suggestions + invalid_unprocessed_suggestions
    services.unprocessed_suggestion_service.insert_unprocessed_suggestions(all_suggestions)
    valid_uuids = {s.uuid_value for s in valid_unprocessed_suggestions}

    pulled_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    pulled_uuids = {s.uuid_value for s in pulled_suggestions}
    assert pulled_uuids == valid_uuids
