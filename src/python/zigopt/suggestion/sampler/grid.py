# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import functools

from zigopt.common import *
from zigopt.assignments.build import set_assignments_map_from_dict
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class GridSampler(SuggestionSampler):
  """
    Generates suggestions on a grid. Uses the `grid_values` on each parameter, which is set
    when the experiment was created.
    We will assume that the experiment was created properly initially and has not been edited.
    """

  @staticmethod
  def observation_budget_from_experiment_meta(experiment_meta):
    return functools.reduce(
      lambda x, y: x * y,
      [len(p.grid_values) for p in experiment_meta.all_parameters_unsorted if p.grid_values],
      1,
    )

  def fetch_best_suggestions(self, limit):
    start_index = self.optimization_args.observation_count + len(self.optimization_args.open_suggestions)
    indexes = range(start_index, start_index + limit)
    return [self.get_suggestion(index) for index in indexes]

  def get_suggestion(self, index):
    assignments_map = dict()
    for parameter in self.experiment.all_parameters:
      grid_values = parameter.grid_values
      assert grid_values, "expected grid values to exist"
      assignments_map[parameter.name] = grid_values[index % len(grid_values)]
      index //= len(grid_values)

    suggestion_data = SuggestionData()
    set_assignments_map_from_dict(suggestion_data, assignments_map)

    return UnprocessedSuggestion(
      experiment_id=self.experiment.id,
      source=UnprocessedSuggestion.Source.GRID,
      suggestion_meta=SuggestionMeta(
        suggestion_data=suggestion_data,
      ),
    )
