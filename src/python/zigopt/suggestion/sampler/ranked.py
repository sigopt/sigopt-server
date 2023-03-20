# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.profile.timing import *
from zigopt.sigoptcompute.constant import DEFAULT_QEI_RERANKING_NUM_PADDING_SUGGESTIONS
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class RankedSampler(SuggestionSampler):
  def generate_padding_suggestions(self, num_padding_suggestions):
    random_sampler = RandomSampler(self.services, self.experiment, source=UnprocessedSuggestion.Source.PADDING_RANDOM)
    random_padding_suggestions = random_sampler.generate_random_suggestions(num_padding_suggestions)
    return random_sampler.append_task_to_suggestions_if_needed_and_missing(random_padding_suggestions)

  def rank_suggestions_with_padding_excluding_low_score(self, suggestions):
    num_random_suggestions = self.services.config_broker.get(
      "model.random_padding_suggestions",
      default=DEFAULT_QEI_RERANKING_NUM_PADDING_SUGGESTIONS,
    )
    random_padding_suggestions = self.generate_padding_suggestions(num_random_suggestions)
    ranked_suggestions = self.services.suggestion_ranker.get_ranked_suggestions_excluding_low_score(
      suggestions,
      self.optimization_args,
      random_padding_suggestions,
    )
    return ranked_suggestions

  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, *args, **kwargs: {"experiment": str(self.experiment.id)},
  )
  def fetch_best_suggestions(self, limit):
    if limit == 0:
      return []

    suggestions = self.generate_suggestions(limit)
    self.services.logging_service.getLogger("suggestions.constant_liar").info(
      "Experiment_id = %s, Constant liar suggestions length = %s", self.experiment.id, len(suggestions)
    )
    return self.rank_suggestions_with_padding_excluding_low_score(suggestions)[:limit]

  def generate_suggestions(self, limit):
    raise NotImplementedError()
