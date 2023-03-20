# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.assignments.build import set_assignments_map_from_dict
from zigopt.optimize.categorical import all_categorical_value_combos
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionMeta
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class CategoricalOnlySampler(SuggestionSampler):
  @generator_to_list
  def fetch_best_suggestions(self, limit):
    all_combos = all_categorical_value_combos(self.experiment.all_parameters)

    open_combos = [s.get_assignments(self.experiment) for s in self.optimization_args.open_suggestions]
    observed_combos = [o.get_assignments(self.experiment) for o in self.optimization_args.observation_iterator]
    sampled_combos = [frozenset(assignments_map.items()) for assignments_map in open_combos + observed_combos]

    unsampled = list(set(all_combos).difference(set(sampled_combos)))

    unsampled_to_take = min(limit, len(unsampled))
    remaining = len(all_combos) - unsampled_to_take
    combos = non_crypto_random.sample(unsampled, unsampled_to_take) + [
      non_crypto_random.choice(all_combos) for _ in range(remaining)
    ]

    for combo in combos[:limit]:
      meta = SuggestionMeta()
      set_assignments_map_from_dict(meta.suggestion_data, dict(combo))
      suggestion = UnprocessedSuggestion(
        experiment_id=self.experiment.id,
        source=UnprocessedSuggestion.Source.EXPLICIT_RANDOM,
        suggestion_meta=(meta),
      )
      yield suggestion
