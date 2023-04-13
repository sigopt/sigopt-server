# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.math.initialization import get_low_discrepancy_stencil_length_from_experiment
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta
from zigopt.services.base import Service
from zigopt.suggestion.lib import CouldNotProcessSuggestionError, SuggestionAlreadyProcessedError
from zigopt.suggestion.sampler.base import SequentialSampler, SuggestionSampler
from zigopt.suggestion.sampler.categorical import CategoricalOnlySampler
from zigopt.suggestion.sampler.grid import GridSampler
from zigopt.suggestion.sampler.lhc import LatinHypercubeSampler
from zigopt.suggestion.sampler.queue import SuggestionQueueSampler
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.sampler.xgb_sampler import XGBSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class BaseBroker(Service):
  def serve_suggestion(self, experiment, processed_suggestion_meta, auth, automatic=False):
    queued_suggestion = self.retrieve_queued_suggestions_if_exists(
      experiment, processed_suggestion_meta, automatic=automatic
    )
    if queued_suggestion is not None:
      return queued_suggestion

    next_suggestion = self.next_suggestion(experiment, processed_suggestion_meta, automatic=automatic)

    return self.replace_with_random_if_necessary(experiment, processed_suggestion_meta, next_suggestion)

  def retrieve_queued_suggestions_if_exists(self, experiment, processed_suggestion_meta, automatic=False):
    for _ in range(self.services.config_broker.get("features.maxQueuedSuggestionFetches", 3)):
      queued_suggestion = self.services.queued_suggestion_service.find_next(experiment.id)
      if not queued_suggestion:
        break
      unprocessed_suggestion = self.services.queued_suggestion_service.create_unprocessed_suggestion(
        experiment,
        queued_suggestion,
      )
      try:
        return self.process_suggestion(
          experiment=experiment,
          unprocessed_suggestion=unprocessed_suggestion,
          processed_suggestion_meta=processed_suggestion_meta,
          queued_id=queued_suggestion.id,
          automatic=automatic,
        )
      except SuggestionAlreadyProcessedError:
        continue
    else:
      raise CouldNotProcessSuggestionError()
    # This is only accessible in the break case up above
    return None

  def next_suggestion(self, experiment, processed_suggestion_meta, automatic=False):
    raise NotImplementedError()

  def allow_random_replacement_on_conflict(self, experiment):
    return experiment.can_generate_fallback_suggestions and not experiment.development

  # NOTE: If the user requests two suggestions at the same time, it is possible but unlikely that
  # they match. This is because the check for duplicate suggestions is executed before they are inserted,
  # and then we could have two processes that insert matching suggestions at the same time.
  # So, if this happens, fix it, by replacing with random. This is a bit of a hack, but it should prevent
  # duplicate suggestions from being seen. However, it is also possible that we turn *both* duplicate
  # suggestions into random. This is not ideal. A perfect solution would prevent this whole situation,
  # perhaps with transactions or a more robust way of ensuring that a suggestion is served only once.
  # However, this should be a rare occurrence, so the random fallback is appropriate
  def replace_with_random_if_necessary(self, experiment, processed_suggestion_meta, next_suggestion):
    if self.allow_random_replacement_on_conflict(experiment):
      conflicting_suggestion = self.services.processed_suggestion_service.find_matching_open_suggestion(
        experiment,
        next_suggestion,
      )
      if conflicting_suggestion:
        next_suggestion = self.services.processed_suggestion_service.replace_unprocessed(
          experiment,
          processed_suggestion=next_suggestion.processed,
          replacement_unprocessed=self.fallback_unprocessed_suggestion(
            experiment,
            processed_suggestion_meta,
            source=UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM,
          ),
        )
    return next_suggestion

  @property
  def only_positive_lds(self):
    raise NotImplementedError()

  def fallback_unprocessed_suggestion(self, experiment, processed_suggestion_meta, source=None):
    source = source or UnprocessedSuggestion.Source.UNKNOWN_FALLBACK_RANDOM
    fallback_sampler = RandomSampler(self.services, experiment, source)
    fallback_suggestion, _ = fallback_sampler.best_suggestion()

    return fallback_suggestion

  def fallback_suggestion(self, experiment, processed_suggestion_meta, source=None, automatic=False):
    fallback_suggestion = self.fallback_unprocessed_suggestion(experiment, processed_suggestion_meta, source=source)
    return self.process_suggestion(experiment, fallback_suggestion, processed_suggestion_meta, automatic=automatic)

  def process_suggestion(self, experiment, unprocessed_suggestion, processed_suggestion_meta, **process_kwargs):
    raise NotImplementedError()

  def should_ignore(self, experiment, unprocessed_suggestion, optimization_args):
    if not self.allow_random_replacement_on_conflict(experiment):
      return False
    assignments_to_skip = []
    compare_assignments = unprocessed_suggestion.get_assignments(experiment)
    if self.services.config_broker.get("features.ignoreRepeatedSuggestions", True):
      if not optimization_args:
        return False
      if optimization_args.last_observation:
        assignments_to_skip.append(optimization_args.last_observation.get_assignments(experiment))
      assignments_to_skip.extend([s.get_assignments(experiment) for s in optimization_args.open_suggestions])
      if compare_assignments in assignments_to_skip:
        self.services.logging_service.getLogger("sigopt.suggest.ignore").info(
          "Experiment %s: Ignoring repeated suggestion %s from optimization args",
          experiment.id,
          unprocessed_suggestion.get_assignments(experiment),
        )
        return True

    if self.services.config_broker.get("features.alternateIgnoreRepeatedSuggestions", True):
      matching_suggestion = self.services.processed_suggestion_service.find_matching_suggestion(
        experiment,
        unprocessed_suggestion,
      )
      if matching_suggestion:
        self.services.logging_service.getLogger("sigopt.suggest.ignore").info(
          "Experiment %s: Ignoring repeated suggestion %s due to matching processed suggestion %s",
          experiment.id,
          unprocessed_suggestion.get_assignments(experiment),
          matching_suggestion.suggestion_id,
        )
        return True
      observation = self.services.database_service.first(
        self.services.database_service.query(Observation)
        .filter(Observation.experiment_id == experiment.id)
        .filter(~Observation.data.HasField("deleted"))
        .filter(Observation.data.assignments_map == compare_assignments)
      )
      if observation:
        self.services.logging_service.getLogger("sigopt.suggest.ignore").info(
          "Experiment %s: Ignoring repeated suggestion %s due to matching observation %s",
          experiment.id,
          unprocessed_suggestion.get_assignments(experiment),
          observation.id,
        )
        return True
    return False

  def _low_discrepancy_sampler(
    self,
    experiment,
    optimization_args,
  ):
    if experiment.is_xgb and not experiment.conditionals and not experiment.constraints:
      return XGBSampler(self.services, experiment, optimization_args)

    if self.should_use_random_for_low_discrepancy(experiment):
      return RandomSampler(self.services, experiment, UnprocessedSuggestion.Source.LOW_DISCREPANCY_RANDOM)

    return LatinHypercubeSampler(self.services, experiment, optimization_args)

  # This is required because each entry in the SequentialSampler requires its own args
  # Another option is itertools.tee, but I do not think there will really be any difference here
  # WARNING - This may execute a DB call and store the observations in a list
  #           Use only for small number of observations if memory concerns exist
  def duplicate_optimization_args(self, optimization_args):
    observations = list(optimization_args.observation_iterator)
    first_args_copy = optimization_args.copy_and_set(observation_iterator=observations)
    second_args_copy = optimization_args.copy_and_set(observation_iterator=observations)
    return first_args_copy, second_args_copy

  # NOTE: If we ever reorganize fetch_args, we could change the broker to be able to fetch inside here
  def next_sampler(self, experiment, optimization_args):
    sampler: SuggestionSampler
    if experiment.development or experiment.experiment_type == ExperimentMeta.RANDOM:
      sampler = RandomSampler(self.services, experiment, source=UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    elif experiment.experiment_type == ExperimentMeta.GRID:
      sampler = GridSampler(self.services, experiment, optimization_args)
    elif not experiment.has_non_categorical_parameters:
      sampler = CategoricalOnlySampler(self.services, experiment, optimization_args)
    else:
      stencil_length = get_low_discrepancy_stencil_length_from_experiment(experiment)
      lds_count = stencil_length - optimization_args.observation_count
      num_open_suggestions = len(optimization_args.open_suggestions)
      if experiment.parallel_bandwidth > 1 and num_open_suggestions < experiment.parallel_bandwidth:
        lds_count -= num_open_suggestions

      samplers_with_counts: tuple[tuple[SuggestionSampler, int], ...] = ()
      if lds_count > 0:
        optimization_args, lds_optimization_args = self.duplicate_optimization_args(optimization_args)
        low_discrepancy_sampler = self._low_discrepancy_sampler(experiment, lds_optimization_args)
        samplers_with_counts = tuple([(low_discrepancy_sampler, lds_count)])
      elif self.only_positive_lds:
        return None

      suggestion_sampler = SuggestionQueueSampler(self.services, experiment, optimization_args)

      samplers_with_counts += tuple([(suggestion_sampler, 1)])
      sampler = SequentialSampler(self.services, experiment, samplers_with_counts)

    return sampler

  def should_use_random_for_low_discrepancy(self, experiment):
    return self.services.optimizer.should_use_spe(experiment, 0) or experiment.has_prior or experiment.has_constraints
