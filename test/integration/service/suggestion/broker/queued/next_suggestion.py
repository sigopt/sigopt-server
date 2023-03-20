# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock, patch

from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


class CustomException(Exception):
  pass


class TestNextSuggestion(SuggestionBrokerTestBase):
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_next_suggestion(
    self,
    services,
    experiment,
    processed_suggestion_meta,
    num_open_suggestions,
  ):
    self.populate_db_with_open_suggestions(
      services,
      experiment,
      num_open_suggestions,
    )

    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment, p1=-10)
    services.suggestion_broker.suggestion_to_serve_next = Mock(
      return_value=(unprocessed_suggestion, dict()),
    )
    suggestion = services.suggestion_broker.next_suggestion(
      experiment=experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    )
    assert suggestion.get_assignments(experiment) == unprocessed_suggestion.get_assignments(experiment)
    if processed_suggestion_meta.HasField("client_provided_data"):
      assert suggestion.client_provided_data == processed_suggestion_meta.client_provided_data
    else:
      assert suggestion.client_provided_data is None

  def test_suggestion_already_processed_error(
    self,
    services,
    experiment,
    processed_suggestion_meta,
    optimization_args,
  ):
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    services.suggestion_broker.suggestion_to_serve_next = Mock(
      return_value=(unprocessed_suggestion, dict()),
    )
    services.optimizer.fetch_optimization_args = Mock(
      return_value=optimization_args,
    )

    services.unprocessed_suggestion_service.process(
      experiment,
      unprocessed_suggestion,
      processed_suggestion_meta,
    )

    suggestion = services.suggestion_broker.next_suggestion(
      experiment=experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    )
    assert suggestion.source == UnprocessedSuggestion.Source.HIGH_CONTENTION_RANDOM

  def test_duplicate_suggestion_fallback_random(
    self,
    services,
    experiment,
    processed_suggestion_meta,
  ):
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    services.unprocessed_suggestion_service.process(
      experiment,
      unprocessed_suggestion,
      processed_suggestion_meta,
    )

    services.suggestion_broker.suggestion_to_serve_next = Mock(
      return_value=(unprocessed_suggestion, dict()),
    )

    suggestion = services.suggestion_broker.next_suggestion(
      experiment=experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    )
    assert suggestion.source == UnprocessedSuggestion.Source.FALLBACK_RANDOM

  def test_ignore(
    self,
    services,
    experiment,
    processed_suggestion_meta,
  ):
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    services.suggestion_broker.suggestion_to_serve_next = Mock(
      return_value=([unprocessed_suggestion], dict()),
    )
    services.suggestion_broker.should_ignore = Mock(return_value=True)

    with patch.object(services.exception_logger, "soft_exception", new_callable=Mock):
      suggestion = services.suggestion_broker.next_suggestion(
        experiment=experiment,
        processed_suggestion_meta=processed_suggestion_meta,
      )

      assert services.exception_logger.soft_exception.call_count == 0
      assert suggestion.source == UnprocessedSuggestion.Source.FALLBACK_RANDOM
      if processed_suggestion_meta.HasField("client_provided_data"):
        assert suggestion.client_provided_data == processed_suggestion_meta.client_provided_data
      else:
        assert suggestion.client_provided_data is None

  def test_no_suggestion(
    self,
    services,
    experiment,
    processed_suggestion_meta,
  ):
    services.suggestion_broker.suggestion_to_serve_next = Mock(
      return_value=(None, dict()),
    )
    with patch.object(services.exception_logger, "soft_exception", new_callable=Mock):
      suggestion = services.suggestion_broker.next_suggestion(
        experiment=experiment,
        processed_suggestion_meta=processed_suggestion_meta,
      )

      assert services.exception_logger.soft_exception.call_count == 0
      assert suggestion.source == UnprocessedSuggestion.Source.FALLBACK_RANDOM
      if processed_suggestion_meta.HasField("client_provided_data"):
        assert suggestion.client_provided_data == processed_suggestion_meta.client_provided_data
      else:
        assert suggestion.client_provided_data is None

  def test_open_suggestions(self, services, parallel_experiment, processed_suggestion_meta, optimization_args):
    # Create 4 open suggestions for problem with parallel_bandwidth = 5
    self.populate_db_with_open_suggestions(services, parallel_experiment, 4)

    # Since the parallel_bandwidth = 5 and there are 4 open suggestions
    # but no observations, we still expect the next source to be LHC
    unprocessed_suggestion, _ = services.suggestion_broker.suggestion_to_serve_next(
      parallel_experiment,
      optimization_args,
    )
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE

    # Add suggestion into the queue
    unprocessed_suggestion = self.new_unprocessed_suggestion(parallel_experiment, p1=-10)
    services.suggestion_broker.suggestion_to_serve_next = Mock(return_value=(unprocessed_suggestion, dict()))
    suggested_assignments = services.suggestion_broker.next_suggestion(
      experiment=parallel_experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    ).get_assignments(parallel_experiment)
    assert suggested_assignments == unprocessed_suggestion.get_assignments(parallel_experiment)

  def test_conditional_assignments(self, services, processed_suggestion_meta):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.conditionals.extend(
      [ExperimentConditional(name="c1", values=[ExperimentConditionalValue(name="cv1")])]
    )
    experiment = self.new_experiment(experiment_meta)
    services.experiment_service.insert(experiment)

    suggestion = services.suggestion_broker.next_suggestion(
      experiment=experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    )

    assert suggestion.source != UnprocessedSuggestion.Source.FALLBACK_RANDOM
    assignments = suggestion.get_assignments(experiment)
    assert len(assignments) == 2
    assert "p1" in assignments
    assert "c1" in assignments
    assert assignments["p1"] is not None
    assert assignments["c1"] is not None
