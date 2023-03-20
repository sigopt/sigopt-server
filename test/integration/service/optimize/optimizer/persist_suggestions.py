# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.optimize.optimizer.test_base import OptimizerServiceTestBase


class TestPersistSuggestions(OptimizerServiceTestBase):
  def test_persist_suggestions(self, services, experiment, unprocessed_suggestions):
    services.optimizer.persist_suggestions(experiment, unprocessed_suggestions)
    redis_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    assert set(u.uuid_value for u in redis_suggestions) == set(u.uuid_value for u in unprocessed_suggestions)

  def test_no_persist_suggestions_on_experiment_delete(self, services, experiment, unprocessed_suggestions):
    services.experiment_service.delete(experiment)
    original_redis = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    services.optimizer.persist_suggestions(experiment, unprocessed_suggestions)
    new_redis = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    assert set(u.uuid_value for u in original_redis) == set(u.uuid_value for u in new_redis)

  @pytest.mark.parametrize("delete_experiment", [True, False])
  def test_no_suggestions(self, services, experiment, delete_experiment):
    if delete_experiment:
      services.experiment_service.delete(experiment)
    services.optimizer.persist_suggestions(experiment, [])
