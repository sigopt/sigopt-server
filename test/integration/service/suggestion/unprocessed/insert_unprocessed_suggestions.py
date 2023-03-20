# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestAddNewRedisSuggestions(UnprocessedSuggestionServiceTestBase):
  def test_insert_unprocessed_suggestions(self, services, experiment):
    source1 = UnprocessedSuggestion.Source.SPE
    source2 = UnprocessedSuggestion.Source.GP_CATEGORICAL
    original_source1_suggestions = [self.new_unprocessed_suggestion(experiment, p1=i, source=source1) for i in range(5)]
    original_source2_suggestions = [self.new_unprocessed_suggestion(experiment, p1=i, source=source2) for i in range(5)]
    expected_source1_uuids = set(s.uuid_value for s in original_source1_suggestions)
    expected_source2_uuids = set(s.uuid_value for s in original_source2_suggestions)
    original_unprocessed_suggestions = original_source1_suggestions + original_source2_suggestions
    services.unprocessed_suggestion_service.insert_unprocessed_suggestions(original_unprocessed_suggestions)

    source1_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment, [source1])
    source1_uuids = set(s.uuid_value for s in source1_suggestions)
    assert source1_uuids == expected_source1_uuids

    source2_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment, [source2])
    source2_uuids = set(s.uuid_value for s in source2_suggestions)
    assert source2_uuids == expected_source2_uuids

  def test_insert_unprocessed_suggestions_truncates_length(self, services, experiment):
    source = UnprocessedSuggestion.Source.SPE  # doesn't matter which
    backlog_multiplier = services.config_broker.get("model.backlog_multiplier", default=3)
    num_suggestions = services.config_broker.get("model.num_suggestions", default=5)
    batches = [
      [self.new_unprocessed_suggestion(experiment, p1=i, source=source) for i in range(num_suggestions)]
      for _ in range(backlog_multiplier + 1)
    ]

    for batch in batches:
      services.unprocessed_suggestion_service.insert_unprocessed_suggestions(batch)

    # we expect to truncate the first batch from redis
    expected_uuids = set(s.uuid_value for batch in batches[1:] for s in batch)

    suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    uuids = set(s.uuid_value for s in suggestions)
    assert uuids == expected_uuids
