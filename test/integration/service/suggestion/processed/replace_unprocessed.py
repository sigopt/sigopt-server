# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.processed.test_base import ProcessedSuggestionServiceTestBase


class TestReplaceUnprocessed(ProcessedSuggestionServiceTestBase):
  def test_replace_unprocessed(self, services, experiment, suggestion):
    old_id = suggestion.id
    source = UnprocessedSuggestion.Source.FALLBACK_RANDOM
    new_unprocessed = self.new_unprocessed_suggestion(experiment, source=source)
    new_suggestion = services.processed_suggestion_service.replace_unprocessed(
      experiment,
      suggestion.processed,
      new_unprocessed,
    )
    new_id = new_unprocessed.id
    assert new_suggestion.unprocessed == new_unprocessed
    assert new_suggestion.id == new_unprocessed.id

    assert new_suggestion.processed == suggestion.processed
    assert new_suggestion.processed.suggestion_id != old_id
    assert new_suggestion.processed.suggestion_id == new_id

    assert services.processed_suggestion_service.find_by_id(old_id) is None
    assert services.processed_suggestion_service.find_by_id(new_id) is not None
    assert services.unprocessed_suggestion_service.find_by_id(new_id) is not None
