# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestFindById(UnprocessedSuggestionServiceTestBase):
  def test_find_by_id(self, services, experiment, unprocessed_suggestion, include_deleted):
    found_suggestion = services.unprocessed_suggestion_service.find_by_id(
      unprocessed_suggestion.id,
      include_deleted=include_deleted,
    )
    assert found_suggestion.id == unprocessed_suggestion.id
    assert found_suggestion.experiment_id == unprocessed_suggestion.experiment_id
    assert found_suggestion.source == unprocessed_suggestion.source
    assert found_suggestion.deleted == unprocessed_suggestion.deleted
    found_assignments = found_suggestion.get_assignments(experiment)
    original_assignments = unprocessed_suggestion.get_assignments(experiment)
    assert found_assignments == original_assignments
    assert found_suggestion.is_valid(experiment) == unprocessed_suggestion.is_valid(experiment)

  def test_cannot_find_deleted(self, services, experiment, unprocessed_suggestion):
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestion.id)
    assert (
      services.unprocessed_suggestion_service.find_by_id(
        unprocessed_suggestion.id,
        include_deleted=False,
      )
      is None
    )

  def test_can_find_deleted(self, services, experiment, unprocessed_suggestion):
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestion.id)
    found_suggestion = services.unprocessed_suggestion_service.find_by_id(
      unprocessed_suggestion.id,
      include_deleted=True,
    )
    assert found_suggestion.id == unprocessed_suggestion.id
    assert found_suggestion.experiment_id == unprocessed_suggestion.experiment_id
    assert found_suggestion.source == unprocessed_suggestion.source
    found_assignments = found_suggestion.get_assignments(experiment)
    original_assignments = unprocessed_suggestion.get_assignments(experiment)
    assert found_assignments == original_assignments
    assert found_suggestion.is_valid(experiment) == unprocessed_suggestion.is_valid(experiment)

    # See note in test.integration.service.suggestion.unprocessed.delete_by_id
    assert found_suggestion.deleted is True
    assert unprocessed_suggestion.deleted is False

  @pytest.mark.parametrize("suggestion_id", [None, 0])
  def test_invalid_id(self, services, suggestion_id, include_deleted):
    assert (
      services.unprocessed_suggestion_service.find_by_id(
        suggestion_id,
        include_deleted=include_deleted,
      )
      is None
    )

  def test_non_existent_id(self, services, unprocessed_suggestion, include_deleted):
    assert (
      services.unprocessed_suggestion_service.find_by_id(
        unprocessed_suggestion.id + 1,
        include_deleted=include_deleted,
      )
      is None
    )
