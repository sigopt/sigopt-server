# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestFindByExperiment(UnprocessedSuggestionServiceTestBase):
  def find_by_experiment(self, services, experiment, unprocessed_suggestions, include_deleted):
    found_suggestions = services.unprocessed_suggestion_service.find_by_experiment(experiment, include_deleted)
    assert len(found_suggestions) == len(unprocessed_suggestions)
    for found_suggestion, unprocessed_suggestion in zip(found_suggestions, unprocessed_suggestions):
      assert found_suggestion.id == unprocessed_suggestion.id
      assert found_suggestion.experiment_id == unprocessed_suggestion.experiment_id
      assert found_suggestion.source == unprocessed_suggestion.source
      assert found_suggestion.deleted == unprocessed_suggestion.deleted
      found_assignments = found_suggestion.get_assignments(experiment)
      original_assignments = unprocessed_suggestion.get_assignments(experiment)
      assert found_assignments == original_assignments
      assert found_suggestion.is_valid(experiment) == unprocessed_suggestion.is_valid(experiment)

  def test_cannot_find_after_delete(self, services, experiment, unprocessed_suggestions):
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    assert services.unprocessed_suggestion_service.find_by_experiment(experiment) == []

  def test_can_find_after_delete(self, services, experiment, unprocessed_suggestions):
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    found_suggestions = services.unprocessed_suggestion_service.find_by_experiment(
      experiment,
      include_deleted=True,
    )
    assert len(found_suggestions) == len(unprocessed_suggestions)

  def test_multiple_experiments(self, services, experiment, unprocessed_suggestions, include_deleted):
    experiment2 = self.new_experiment()
    services.experiment_service.insert(experiment2)
    u2 = self.new_unprocessed_suggestion(experiment2)
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([u2])

    found_suggestions = services.unprocessed_suggestion_service.find_by_experiment(experiment, include_deleted)
    assert len(found_suggestions) == len(unprocessed_suggestions)

  def test_no_suggestions(self, services, experiment, include_deleted):
    assert services.unprocessed_suggestion_service.find_by_experiment(experiment, include_deleted) == []

  def test_invalid_experiment(self, services, include_deleted):
    with pytest.raises(Exception):
      services.unprocessed_suggestion_service.find_by_experiment(None, include_deleted)
