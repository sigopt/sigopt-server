# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

import pytest
from mock import MagicMock, Mock

from zigopt.optimize.args import OptimizationArgs
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


class TestSuggestionToServeNext(SuggestionBrokerTestBase):
  @pytest.mark.slow
  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_uses_sampler(self, services, num_observations, num_open_suggestions, optimization_args):
    mock_unprocessed_suggestion = Mock()
    mock_kwargs = MagicMock()
    blank_kwargs: dict[str, Any] = {}
    mock_kwargs.__getitem__.side_effect = blank_kwargs.__getitem__
    mock_kwargs.__iter__.side_effect = blank_kwargs.__iter__
    mock_kwargs.__contains__.side_effect = blank_kwargs.__contains__
    mock_sampler = Mock(best_suggestion=Mock(return_value=(mock_unprocessed_suggestion, mock_kwargs)))

    services.queued_suggestion_service.find_next = Mock(return_value=None)
    services.suggestion_service.find_open_by_experiment = Mock(return_value=[])
    services.suggestion_broker.next_sampler = Mock(return_value=mock_sampler)

    # We use a real experiment to put observations in the DB
    e = self.new_experiment()
    services.experiment_service.insert(e)
    self.populate_db_with_observations(services, e, num_observations)
    e = self.new_experiment()
    services.experiment_service.insert(e)
    self.populate_db_with_open_suggestions(services, e, num_open_suggestions)

    experiment = Mock(
      id=1,
      client_id=1,
    )
    unprocessed_suggestion, kwargs = services.suggestion_broker.suggestion_to_serve_next(experiment, optimization_args)

    assert unprocessed_suggestion is mock_unprocessed_suggestion
    assert kwargs is mock_kwargs

    args = services.suggestion_broker.next_sampler.call_args[0]
    assert args[0] is experiment
    assert isinstance(args[1], OptimizationArgs)

  def test_simple(self, services, experiment, optimization_args):
    unprocessed_suggestion, kwargs = services.suggestion_broker.suggestion_to_serve_next(experiment, optimization_args)
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE
    assert kwargs == {}
