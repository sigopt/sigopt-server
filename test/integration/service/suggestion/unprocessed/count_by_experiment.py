# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestCountByExperiment(UnprocessedSuggestionServiceTestBase):
  def count_by_experiment(self, services, experiment, unprocessed_suggestions, include_deleted):
    count = services.unprocessed_suggestion_service.count_by_experiment(experiment, include_deleted)
    assert count == len(unprocessed_suggestions)

  def test_cannot_find_after_delete(self, services, experiment, unprocessed_suggestions):
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    assert services.unprocessed_suggestion_service.count_by_experiment(experiment) == 0

  def test_can_find_after_delete(self, services, experiment, unprocessed_suggestions):
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    count = services.unprocessed_suggestion_service.count_by_experiment(
      experiment,
      include_deleted=True,
    )
    assert count == len(unprocessed_suggestions)

  def test_multiple_experiments(self, services, experiment, unprocessed_suggestions, include_deleted):
    experiment2 = self.new_experiment()
    services.experiment_service.insert(experiment2)
    u2 = self.new_unprocessed_suggestion(experiment2)
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([u2])

    count = services.unprocessed_suggestion_service.count_by_experiment(experiment, include_deleted)
    assert count == len(unprocessed_suggestions)

  def test_no_suggestions(self, services, experiment, include_deleted):
    assert services.unprocessed_suggestion_service.count_by_experiment(experiment, include_deleted) == 0

  def test_invalid_experiment(self, services, include_deleted):
    with pytest.raises(Exception):
      services.unprocessed_suggestion_service.count_by_experiment(None, include_deleted)
