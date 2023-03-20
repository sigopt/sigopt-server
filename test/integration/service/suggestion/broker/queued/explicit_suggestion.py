# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


class TestExplicitSuggestion(SuggestionBrokerTestBase):
  @pytest.fixture(params=[-20, -10, 0, 10, 20])
  def suggestion_meta(self, request):
    return SuggestionMeta(
      suggestion_data=SuggestionData(
        assignments_map=dict(p1=request.param),
      ),
    )

  def test_explicit_suggestion(self, services, experiment, suggestion_meta, processed_suggestion_meta):
    suggestion = services.suggestion_broker.explicit_suggestion(experiment, suggestion_meta, processed_suggestion_meta)
    assert suggestion.source == UnprocessedSuggestion.Source.USER_CREATED
    assert suggestion.experiment_id == experiment.id
    assert suggestion.get_assignments(experiment) == dict(p1=suggestion_meta.suggestion_data.assignments_map["p1"])
    if processed_suggestion_meta.HasField("client_provided_data"):
      assert suggestion.client_provided_data == processed_suggestion_meta.client_provided_data
    else:
      assert suggestion.client_provided_data is None
