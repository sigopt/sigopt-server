# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from zigopt.optimize.sources.base import OptimizationSource
from zigopt.protobuf.gen.optimize.sources_pb2 import NullHyperparameters
from zigopt.suggestion.lib import ScoredSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


SUCCESS_OBSERVATIONS_FOR_SPE_NEXT_POINTS = 1


class SPEOptimizationSource(OptimizationSource):
  hyperparameter_type = NullHyperparameters
  name = "spe"

  def __init__(self, services, experiment):
    super().__init__(services, experiment)

  def get_suggestions(self, optimization_args, limit=None):
    if optimization_args.observation_count - optimization_args.failure_count < SUCCESS_OBSERVATIONS_FOR_SPE_NEXT_POINTS:
      return []

    if self.experiment.is_search or self.experiment.num_solutions > 1:
      return self.get_search_suggestions(optimization_args, limit)

    immutable_suggestion_datas = self.services.sc_adapter.spe_next_points(
      experiment=self.experiment,
      observation_iterator=optimization_args.observation_iterator,
      num_to_suggest=self.coalesce_num_to_suggest(limit),
      observation_count=optimization_args.observation_count,
      open_suggestion_datas=self.extract_open_suggestion_datas(optimization_args),
      tag=None,
    )

    return self.create_unprocessed_suggestions(
      immutable_suggestion_datas,
      source_number=UnprocessedSuggestion.Source.SPE,
    )

  def get_search_suggestions(self, optimization_args, limit=None):
    immutable_suggestion_datas = self.services.sc_adapter.spe_search_next_points(
      experiment=self.experiment,
      observation_iterator=optimization_args.observation_iterator,
      num_to_suggest=self.coalesce_num_to_suggest(limit),
      observation_count=optimization_args.observation_count,
      open_suggestion_datas=self.extract_open_suggestion_datas(optimization_args),
      tag=None,
    )
    return self.create_unprocessed_suggestions(
      immutable_suggestion_datas,
      source_number=UnprocessedSuggestion.Source.SPE_SEARCH,
    )

  # TODO(RTL-121): Will need to further propagate the no-enqueue to allow this to raise an error.
  def get_hyperparameters(self, optimization_args):
    return NullHyperparameters()

  def get_scored_suggestions(self, suggestions, optimization_args, random_padding_suggestions):
    return [ScoredSuggestion(s, s.generated_time) for s in suggestions]

  def construct_initial_hyperparameters(self):
    return None

  def should_execute_hyper_opt(self, num_successful_observations):
    return False
