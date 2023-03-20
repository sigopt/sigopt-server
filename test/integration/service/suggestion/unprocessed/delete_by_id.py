# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestDeleteById(UnprocessedSuggestionServiceTestBase):
  def test_delete_by_id(self, services, experiment, unprocessed_suggestion):
    assert unprocessed_suggestion.deleted is False
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestion.id)
    # We update by id so we don't expect the object to update
    assert unprocessed_suggestion.deleted is False

  def test_find_after_delete(self, services, experiment, unprocessed_suggestion):
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestion.id)

    assert services.unprocessed_suggestion_service.find_by_id(unprocessed_suggestion.id) is None
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(
      unprocessed_suggestion.id,
      include_deleted=True,
    )
    assert unprocessed_suggestion.deleted is True

  @pytest.mark.parametrize("suggestion_id", [None, 0])
  def test_invalid_id(self, services, experiment, suggestion_id):
    services.unprocessed_suggestion_service.delete_by_id(experiment, suggestion_id)

  def test_non_existent_id(self, services, experiment, unprocessed_suggestion):
    services.unprocessed_suggestion_service.delete_by_id(experiment, unprocessed_suggestion.id + 1)
