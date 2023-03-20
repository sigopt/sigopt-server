# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import patch

from zigopt.authorization.user import UserAuthorization
from zigopt.exception.logger import SoftException
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase
from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class TestProcessRedisSuggestion(
  UnprocessedSuggestionServiceTestBase,
  SuggestionBrokerTestBase,
):
  @pytest.fixture
  def auth(self):
    return UserAuthorization(current_user=None, user_token=None, scoped_membership=None, scoped_permission=None)

  def test_remove_from_available_suggestions(self, services, experiment):
    source = UnprocessedSuggestion.Source.SPE
    original_unprocessed_suggestions = [
      self.new_unprocessed_suggestion(experiment, p1=i, source=source) for i in range(5)
    ]
    expected_all_uuids = set(s.uuid_value for s in original_unprocessed_suggestions)
    services.unprocessed_suggestion_service.insert_unprocessed_suggestions(original_unprocessed_suggestions)

    # confirm we have all suggestions prior to processing
    suggestions_before_processing = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    all_uuids = set(s.uuid_value for s in suggestions_before_processing)
    assert all_uuids == expected_all_uuids

    # process arbitrary suggestion
    suggestion = original_unprocessed_suggestions[0]
    services.unprocessed_suggestion_service.remove_from_available_suggestions(suggestion)

    expected_uuids = expected_all_uuids - set([suggestion.uuid_value])
    suggestions_after_processing = services.unprocessed_suggestion_service.get_suggestions_per_source(experiment)
    uuids = set(s.uuid_value for s in suggestions_after_processing)
    assert uuids == expected_uuids

  def test_not_remove_redis_disabled(self, services, experiment, auth):
    services.config_broker["redis.enabled"] = False
    services.redis_service.redis = None

    # Ensure we can serve suggestions without raising error
    services.config_broker["features.raiseSoftExceptions"] = False
    suggestion = services.suggestion_broker.serve_suggestion(
      experiment=experiment, processed_suggestion_meta=ProcessedSuggestionMeta(), auth=auth
    )
    assert isinstance(suggestion, Suggestion)

    # Ensure we actually are raising a soft exception for logging purposes
    services.config_broker["features.raiseSoftExceptions"] = True
    with pytest.raises(SoftException):
      suggestion = services.suggestion_broker.serve_suggestion(
        experiment=experiment, processed_suggestion_meta=ProcessedSuggestionMeta(), auth=auth
      )

    # Ensure that we can reconnect to redis
    services.config_broker["redis.enabled"] = True
    suggestion = services.suggestion_broker.serve_suggestion(
      experiment=experiment, processed_suggestion_meta=ProcessedSuggestionMeta(), auth=auth
    )
    assert isinstance(suggestion, Suggestion)

  def test_remove_redis_missing(self, services, experiment, auth):
    with patch.object(services.redis_service, "remove_from_hash") as remove_from_hash_mock:
      remove_from_hash_mock.side_effect = Exception

      services.config_broker["features.raiseSoftExceptions"] = False
      suggestion = services.suggestion_broker.serve_suggestion(
        experiment=experiment, processed_suggestion_meta=ProcessedSuggestionMeta(), auth=auth
      )
      assert isinstance(suggestion, Suggestion)
      assert remove_from_hash_mock.call_count == 1

      services.config_broker["features.raiseSoftExceptions"] = True
      with pytest.raises(SoftException):
        suggestion = services.suggestion_broker.serve_suggestion(
          experiment=experiment, processed_suggestion_meta=ProcessedSuggestionMeta(), auth=auth
        )
      assert remove_from_hash_mock.call_count == 2
