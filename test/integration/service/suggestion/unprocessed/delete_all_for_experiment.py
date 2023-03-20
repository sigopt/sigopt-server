# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestDeleteAllForExperiment(UnprocessedSuggestionServiceTestBase):
  def test_delete_all_for_experiment(self, services, experiment, unprocessed_suggestions):
    assert all(not u.deleted for u in unprocessed_suggestions)
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    # We update by experiment info so we don't expect these objects to update
    assert all(not u.deleted for u in unprocessed_suggestions)

  def test_find_after_delete(self, services, experiment, unprocessed_suggestions):
    ids = [u.id for u in unprocessed_suggestions]
    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment)
    assert services.unprocessed_suggestion_service.find_by_ids(ids) == []
    unprocessed_suggestions = services.unprocessed_suggestion_service.find_by_ids(ids, include_deleted=True)
    assert len(unprocessed_suggestions) == 3
    assert all(u.deleted for u in unprocessed_suggestions)

  def test_multiple_experiments(self, services, experiment, unprocessed_suggestions):
    ids = [u.id for u in unprocessed_suggestions]

    experiment2 = self.new_experiment()
    services.experiment_service.insert(experiment2)

    services.unprocessed_suggestion_service.delete_all_for_experiment(experiment2)

    unprocessed_suggestions = services.unprocessed_suggestion_service.find_by_ids(ids)
    assert all(not u.deleted for u in unprocessed_suggestions)
