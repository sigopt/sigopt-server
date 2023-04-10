# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.context import EmptyContext
from zigopt.suggestion.broker.base import BaseBroker
from zigopt.suggestion.lib import CouldNotProcessSuggestionError, SuggestionAlreadyProcessedError
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class SuggestionBroker(BaseBroker):
  def suggestion_to_serve_next(self, experiment, optimization_args, skip=0):
    sampler = self.next_sampler(experiment, optimization_args)
    unprocessed_suggestion, process_kwargs = sampler.best_suggestion(skip=skip)
    return unprocessed_suggestion, process_kwargs

  def next_suggestion(self, experiment, processed_suggestion_meta, automatic=False):
    fallback_source = UnprocessedSuggestion.Source.FALLBACK_RANDOM

    with (
      EmptyContext()
      if self.services.config_broker.get("queue.forbid_random_fallback", False)
      else self.services.exception_logger.tolerate_exceptions(Exception)
    ):
      old_did_force_hitandrun = experiment.force_hitandrun_sampling
      suggestions_to_skip = 0
      for _ in range(5):
        optimization_args = self.services.optimizer.fetch_optimization_args(experiment)
        unprocessed_suggestion, process_kwargs = self.suggestion_to_serve_next(
          experiment,
          optimization_args,
          skip=suggestions_to_skip,
        )

        if unprocessed_suggestion is None:
          break
        if self.should_ignore(experiment, unprocessed_suggestion, optimization_args):
          suggestions_to_skip += 1
          continue
        try:
          # Persist changes to hitandrun flag
          if not old_did_force_hitandrun and experiment.force_hitandrun_sampling:
            self.services.experiment_service.force_hitandrun_sampling(experiment, True)

          return self.process_suggestion(
            experiment, unprocessed_suggestion, processed_suggestion_meta, automatic=automatic, **process_kwargs
          )
        except SuggestionAlreadyProcessedError:
          # edge-case: during first (successful) process, error before remove_from_available_suggestions()
          # this acts as safe-guard so we don't keep trying to return already-processed suggestion
          self.services.unprocessed_suggestion_service.remove_from_available_suggestions(unprocessed_suggestion)
          fallback_source = UnprocessedSuggestion.Source.HIGH_CONTENTION_RANDOM
          continue

    if not experiment.can_generate_fallback_suggestions:
      raise CouldNotProcessSuggestionError()
    # fallback to random to minimize user API errors
    return self.fallback_suggestion(experiment, processed_suggestion_meta, source=fallback_source, automatic=automatic)

  def process_suggestion(self, experiment, unprocessed_suggestion, processed_suggestion_meta, **process_kwargs):
    return self.services.unprocessed_suggestion_service.process(
      experiment=experiment,
      unprocessed_suggestion=unprocessed_suggestion,
      processed_suggestion_meta=processed_suggestion_meta,
      **process_kwargs
    )

  def explicit_suggestion(self, experiment, suggestion_meta, processed_suggestion_meta, automatic=False):
    unprocessed_suggestion = UnprocessedSuggestion(
      experiment_id=experiment.id,
      source=UnprocessedSuggestion.Source.USER_CREATED,
      suggestion_meta=suggestion_meta,
    )
    return self.process_suggestion(experiment, unprocessed_suggestion, processed_suggestion_meta, automatic=automatic)

  @property
  def only_positive_lds(self):
    return False
