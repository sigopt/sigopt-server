# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.conditionals.util import convert_to_unconditioned_experiment
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.unprocessed.model import SuggestionDataProxy, UnprocessedSuggestion


class ConditionalOptimizationSource(CategoricalOptimizationSource):
  name = "conditional"

  # NOTE: We store both the original experiment and the unconditioned experiment.
  #       self.experiment is set to the unconditioned experiment to reuse all the
  #       functions from CategoricalOptimizationSource
  def __init__(self, services, experiment):
    super().__init__(services, experiment)
    self._conditioned_experiment = experiment
    self.experiment = convert_to_unconditioned_experiment(experiment)

  def get_suggestions(self, optimization_args, limit=None):
    if self.is_suitable_at_this_point(optimization_args.observation_count):
      source_number = UnprocessedSuggestion.Source.GP_CATEGORICAL
      unconditioned_suggestions = super().get_suggestions(optimization_args, limit)
    else:
      source_number = UnprocessedSuggestion.Source.EXPLICIT_RANDOM
      sampler = RandomSampler(self.services, self.experiment, source_number)
      unconditioned_suggestions = sampler.generate_random_suggestion_datas(count=1)

    conditioned_suggestion_proxies = self._filter_conditioned_suggestion_proxies(unconditioned_suggestions)

    return self.create_unprocessed_suggestions(
      conditioned_suggestion_proxies,
      source_number,
    )

  def _filter_conditioned_suggestion_proxies(self, unconditioned_suggestions):
    conditioned_suggestion_data_proxies = []
    for s in unconditioned_suggestions:
      conditioned_suggestion_data_proxies.append(
        SuggestionDataProxy(
          SuggestionData(assignments_map=s.get_assignments(self._conditioned_experiment), task=s.task)
        )
      )
    return conditioned_suggestion_data_proxies
