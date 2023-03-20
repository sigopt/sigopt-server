# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.sigoptcompute.constant import MINIMUM_SUCCESSES_TO_COMPUTE_EI
from zigopt.suggestion.lib import ScoredSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


"""
This class will score suggestions based on a GPs similar to CategoricalOptimizationSource,
we only change the scoring strategy. All hyperparameter calls are exactly the same.
"""


class SearchOptimizationSource(CategoricalOptimizationSource):
  name = "search"

  def should_have_task_length(self):
    return False

  def get_suggestions(self, optimization_args, limit=None):
    if optimization_args.observation_count - optimization_args.failure_count < MINIMUM_SUCCESSES_TO_COMPUTE_EI:
      return []

    suggestion_datas = self.services.sc_adapter.search_next_points(
      experiment=self.experiment,
      observations=list(optimization_args.observation_iterator),
      hyperparameter_dict=self.extract_hyperparameter_dict(optimization_args),
      num_to_suggest=self.coalesce_num_to_suggest(self.default_limit(limit)),
      open_suggestion_datas=self.extract_open_suggestion_datas(optimization_args),
    )

    return self.create_unprocessed_suggestions(
      suggestion_data_proxies=suggestion_datas,
      source_number=UnprocessedSuggestion.Source.SEARCH,
    )

  def get_scored_suggestions(self, suggestions, optimization_args, random_padding_suggestions):
    return [ScoredSuggestion(s, s.generated_time) for s in suggestions]
