# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta

from integration.service.suggestion.unprocessed.test_base import UnprocessedSuggestionServiceTestBase


class ProcessedSuggestionServiceTestBase(UnprocessedSuggestionServiceTestBase):
  @pytest.fixture
  def suggestion(self, services, experiment, unprocessed_suggestion):
    return services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=ProcessedSuggestionMeta(),
    )
