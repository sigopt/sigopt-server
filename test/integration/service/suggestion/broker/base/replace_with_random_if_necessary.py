# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from mock import Mock

from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


class TestReplaceWithRandomIfNecessary(SuggestionBrokerTestBase):
  def test_next_suggestion_race_condition(self, services, experiment):
    self.populate_db_with_observations(services, experiment, 4)
    p1 = 9.01
    assignments = {"p1": p1}

    # Mock suggestion_ranker, to prevent suggestions from getting dropped
    services.suggestion_ranker.get_ranked_suggestions_excluding_low_score = (
      lambda suggestions, optimization_args, random_padding_suggestions: suggestions
    )

    suggestions = []
    for _ in range(2):
      optimization_args = services.optimizer.fetch_optimization_args(experiment)
      services.unprocessed_suggestion_service.insert_unprocessed_suggestions(
        [self.new_unprocessed_suggestion(experiment, p1=p1)],
      )
      (unprocessed_suggestion, process_kwargs) = services.suggestion_broker.suggestion_to_serve_next(
        experiment,
        optimization_args,
        skip=0,
      )
      suggestion = services.suggestion_broker.process_suggestion(
        experiment, unprocessed_suggestion, ProcessedSuggestionMeta(), **process_kwargs
      )
      suggestions.append(suggestion)

    (s1, s2) = (suggestions[0], suggestions[1])
    assert s1.unprocessed.get_assignments(experiment) == assignments
    assert s2.unprocessed.get_assignments(experiment) == assignments
    assert s1.source != UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM

    next_suggestion = services.suggestion_broker.replace_with_random_if_necessary(
      experiment,
      ProcessedSuggestionMeta(),
      s1,
    )
    assert next_suggestion.source == UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM
    assert next_suggestion.id == s1.id
    assert next_suggestion.observation is None
    assert next_suggestion.experiment_id == experiment.id

  def test_race_condition_with_mock(self, services, experiment):
    services.processed_suggestion_service.find_matching_open_suggestion = Mock(return_value=Mock())
    processed_suggestion_meta = ProcessedSuggestionMeta()
    next_suggestion = services.suggestion_broker.next_suggestion(
      experiment=experiment,
      processed_suggestion_meta=processed_suggestion_meta,
    )
    assert next_suggestion.source != UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM
    next_suggestion = services.suggestion_broker.replace_with_random_if_necessary(
      experiment, processed_suggestion_meta, next_suggestion
    )
    assert next_suggestion.source == UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM
