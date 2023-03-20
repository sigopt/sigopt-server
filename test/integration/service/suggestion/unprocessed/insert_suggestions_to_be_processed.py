# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestInsertSuggestions(UnprocessedSuggestionServiceTestBase):
  @pytest.fixture
  def unprocessed_suggestions(self, request, services, experiment):
    return [self.new_unprocessed_suggestion(experiment) for _ in range(3)]

  def test_insert_suggestions_to_be_processed(self, services, experiment, unprocessed_suggestions):
    assert all(u.id is None for u in unprocessed_suggestions)
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed(unprocessed_suggestions)
    assert all(u.id is not None for u in unprocessed_suggestions)
    assert len(set(u.id for u in unprocessed_suggestions)) == 3

  def test_can_find(self, services, experiment, unprocessed_suggestions, include_deleted):
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed(unprocessed_suggestions)
    for unprocessed_suggestion in unprocessed_suggestions:
      assert (
        services.unprocessed_suggestion_service.find_by_id(
          unprocessed_suggestion.id,
          include_deleted=include_deleted,
        )
        is not None
      )

  def test_empty_suggestions(self, services):
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([])

  @pytest.mark.parametrize("unprocessed_suggestions", [None, [None]])
  def test_invalid_suggestions(self, services, unprocessed_suggestions):
    with pytest.raises(Exception):
      services.unprocessed_suggestion_service.insert_suggestions_to_be_processed(unprocessed_suggestions)
