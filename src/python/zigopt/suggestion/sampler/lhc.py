# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.assignments.build import set_assignments_map_from_dict
from zigopt.conditionals.util import convert_to_unconditioned_experiment
from zigopt.math.initialization import get_low_discrepancy_stencil_length_from_experiment
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.unprocessed.model import SuggestionDataProxy, UnprocessedSuggestion


# TODO(RTL-124): Think on if we want some more interesting task management in the LHC phase
# NOTE - Creating self.observations may require a DB call which is executed when this sampler is created
class LatinHypercubeSampler(SuggestionSampler):
  source = UnprocessedSuggestion.Source.LATIN_HYPERCUBE

  def __init__(self, services, experiment, optimization_args):
    super().__init__(services, experiment, optimization_args)
    self.is_conditional = False
    if experiment.conditionals:
      self.experiment = convert_to_unconditioned_experiment(experiment)
      self._conditioned_experiment = experiment
      self.is_conditional = True
    self.stencil_length = get_low_discrepancy_stencil_length_from_experiment(self.experiment)
    self.observations = list(self.optimization_args.observation_iterator)

  def build_intervals(self, open_suggestions):
    intervals_by_parameter = {
      p.name: {
        i
        for i in self.services.experiment_parameter_segmenter.segmented_intervals(p, self.stencil_length)
        if self.services.experiment_parameter_segmenter.has_values(p, i)
      }
      for p in self.experiment.all_parameters
    }

    self.services.experiment_parameter_segmenter.prune_intervals(
      self.experiment,
      self.observations + open_suggestions,
      intervals_by_parameter,
    )

    return intervals_by_parameter

  def fetch_best_suggestions(self, limit):
    if not self.is_conditional:
      return self._fetch_best_suggestions(limit)

    unprocessed_suggestions = []
    for unconditioned_suggestion in self._fetch_best_suggestions(limit):
      conditioned_suggestion_data = SuggestionData(
        assignments_map=unconditioned_suggestion.get_assignments(self._conditioned_experiment),
      )
      unprocessed_suggestions.append(self.form_unprocessed_suggestion(data=conditioned_suggestion_data))
    return unprocessed_suggestions

  @property
  def _default_task(self):
    return self.experiment.cheapest_task

  @generator_to_list
  def _fetch_best_suggestions(self, limit):
    intervals_by_parameter = self.build_intervals(self.optimization_args.open_suggestions)
    for _ in range(limit):
      suggestion_data = SuggestionData()

      assignments = dict()
      for parameter in self.experiment.all_parameters:
        intervals = intervals_by_parameter.get(parameter.name)
        assignment = self.services.experiment_parameter_segmenter.pick_value(parameter, intervals)
        assignments[parameter.name] = assignment

      set_assignments_map_from_dict(suggestion_data, assignments)

      self.services.experiment_parameter_segmenter.prune_intervals(
        self.experiment, [SuggestionDataProxy(suggestion_data)], intervals_by_parameter
      )

      yield self.form_unprocessed_suggestion(data=suggestion_data)
