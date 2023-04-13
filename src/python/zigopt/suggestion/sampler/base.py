# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.profile.timing import *
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionMeta
from zigopt.protobuf.lib import CopyFrom
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class SuggestionSampler:
  source: int

  def __init__(self, services, experiment, optimization_args):
    self.services = services
    self.experiment = experiment
    self.optimization_args = optimization_args

  def best_suggestion(self, skip=0):
    process_kwargs: dict = {}
    suggestions = self.fetch_best_suggestions(limit=1 + skip)
    suggestions = suggestions[skip:]
    if not suggestions:
      return None, process_kwargs

    suggestions = self.append_task_to_suggestions_if_needed_and_missing(suggestions)
    return suggestions[0], process_kwargs

  def fetch_best_suggestions(self, limit):
    raise NotImplementedError()

  def form_unprocessed_suggestion(self, data, source=None):
    return UnprocessedSuggestion(
      experiment_id=self.experiment.id,
      source=source or self.source,
      suggestion_meta=SuggestionMeta(suggestion_data=data.copy_protobuf()),
    )

  @property
  def _default_task(self):
    self.services.exception_logger.soft_exception(
      (
        f"Experiment {self.experiment.id} received a suggestion that should have had a task attached, but did"
        f" not.  This sampler is of type {type(self)}."
      ),
    )
    return self.experiment.costliest_task

  def append_task_to_suggestions_if_needed_and_missing(self, suggestions):
    if not (suggestions and self.experiment.is_multitask):
      return suggestions

    for unprocessed_suggestion in suggestions:
      if unprocessed_suggestion.task:
        continue
      suggestion_meta = unprocessed_suggestion.suggestion_meta.copy_protobuf()
      CopyFrom(suggestion_meta.suggestion_data.task, self._default_task.copy_protobuf())
      unprocessed_suggestion.suggestion_meta = suggestion_meta

    return suggestions


# Picks sequentially from a list of samplers
# TODO - Eventually, we should just cut this because we never really use it in the way it is meant to be
class SequentialSampler(SuggestionSampler):
  def __init__(self, services, experiment, samplers_with_counts):
    optimization_args = samplers_with_counts[0][0].optimization_args if samplers_with_counts else None
    super().__init__(services, experiment, optimization_args)
    self.samplers_with_counts = samplers_with_counts

  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, *args, **kwargs: {"experiment": str(self.experiment.id)},
  )
  def fetch_best_suggestions(self, limit):
    ret: list[UnprocessedSuggestion] = []
    for sampler, this_count in self.samplers_with_counts:
      remaining_needed = limit - len(ret)
      this_count = min(remaining_needed, this_count)
      suggestions = sampler.fetch_best_suggestions(this_count)
      suggestions = sampler.append_task_to_suggestions_if_needed_and_missing(suggestions)
      ret.extend(suggestions)
      if len(ret) >= limit:
        break
    return ret[:limit]
