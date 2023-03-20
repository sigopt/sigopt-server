# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestFindByIds(UnprocessedSuggestionServiceTestBase):
  def test_find_by_ids(self, services, experiment, unprocessed_suggestions, include_deleted):
    ids = [u.id for u in unprocessed_suggestions]
    found_suggestions = services.unprocessed_suggestion_service.find_by_ids(
      ids,
      include_deleted=include_deleted,
    )
    assert len(found_suggestions) == len(unprocessed_suggestions)
    for found_suggestion, unprocessed_suggestion in zip(
      sorted(found_suggestions, key=lambda u: u.id),
      sorted(unprocessed_suggestions, key=lambda u: u.id),
    ):
      assert found_suggestion.id == unprocessed_suggestion.id
      assert found_suggestion.experiment_id == unprocessed_suggestion.experiment_id
      assert found_suggestion.source == unprocessed_suggestion.source
      assert found_suggestion.deleted == unprocessed_suggestion.deleted
      found_assignments = found_suggestion.get_assignments(experiment)
      original_assignments = unprocessed_suggestion.get_assignments(experiment)
      assert found_assignments == original_assignments
      assert found_suggestion.is_valid(experiment) == unprocessed_suggestion.is_valid(experiment)

  def test_cannot_find_deleted(self, services, experiment, unprocessed_suggestions):
    ids = [u.id for u in unprocessed_suggestions]
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestions[1].id)
    found_suggestions = services.unprocessed_suggestion_service.find_by_ids(ids)
    assert len(found_suggestions) == len(unprocessed_suggestions) - 1

  def test_can_find_deleted(self, services, experiment, unprocessed_suggestions):
    ids = [u.id for u in unprocessed_suggestions]
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestions[1].id)
    found_suggestions = services.unprocessed_suggestion_service.find_by_ids(ids, include_deleted=True)
    assert len(found_suggestions) == len(unprocessed_suggestions)

  def test_multiple_experiments(self, services, experiment, unprocessed_suggestions, include_deleted):
    ids = [u.id for u in unprocessed_suggestions]

    experiment2 = self.new_experiment()
    services.experiment_service.insert(experiment2)
    u2 = self.new_unprocessed_suggestion(experiment2)
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([u2])

    found_suggestions = services.unprocessed_suggestion_service.find_by_ids(
      ids + [u2.id],
      include_deleted=include_deleted,
    )
    assert len(found_suggestions) == len(unprocessed_suggestions) + 1

  @pytest.mark.parametrize("ids", [[0], [None], []])
  def test_invalid_ids(self, services, experiment, ids, include_deleted):
    assert services.unprocessed_suggestion_service.find_by_ids(ids, include_deleted=include_deleted) == []
