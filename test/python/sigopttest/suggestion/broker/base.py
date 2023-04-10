# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.exception.logger import ExceptionLogger
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.suggestion.broker.queued import SuggestionBroker
from zigopt.suggestion.lib import SuggestionException

from sigopttest.base.config_broker import StrictAccessConfigBroker


class CustomException(Exception):
  pass


class TestNextSuggestion:
  @pytest.fixture
  def suggestion_broker(self, services):
    return SuggestionBroker(services)

  @pytest.fixture
  def services(self):
    services = Mock()
    services.config_broker = StrictAccessConfigBroker.from_configs(
      {
        "features": {"raiseSoftExceptions": False},
        "model": {"force_spe": False},
        "optimize": {"rejection_sampling_trials": 0},
        "queue": {"forbid_random_fallback": False},
      }
    )
    services.exception_logger = ExceptionLogger(services)
    return services

  @pytest.fixture
  def experiment(self):
    return Mock()

  def test_next_suggestion_fails_for_folded_suggestions(
    self,
    services,
    experiment,
    suggestion_broker,
  ):
    experiment.can_generate_fallback_suggestions = False
    suggestion_broker.suggestion_to_serve_next = Mock(side_effect=CustomException())
    with pytest.raises(SuggestionException):
      suggestion_broker.next_suggestion(
        experiment=experiment,
        processed_suggestion_meta=None,
      )

  @pytest.mark.parametrize("random_fallback", [True, False])
  def test_next_suggestion_does_fail(
    self,
    services,
    experiment,
    random_fallback,
    suggestion_broker,
  ):
    services.config_broker["queue.forbid_random_fallback"] = random_fallback
    services.config_broker["features.raiseSoftExceptions"] = True
    suggestion_broker.suggestion_to_serve_next = Mock(side_effect=CustomException())
    with pytest.raises(CustomException):
      suggestion_broker.next_suggestion(
        experiment=experiment,
        processed_suggestion_meta=None,
      )
