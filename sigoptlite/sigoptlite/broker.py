# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigoptaux.constant import DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS, DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS
from sigoptlite.builders import LocalObservationBuilder
from sigoptlite.errors import LocalBadParamError
from sigoptlite.models import LocalSuggestion, dataclass_to_dict
from sigoptlite.sources import GPSource, RandomSearchSource, SPESource


class Broker(object):
  def __init__(self, experiment, force_spe=False):
    self.experiment = experiment
    self.observations = []
    self.stored_suggestion = None
    self.hyperparameters = None
    self.force_spe = force_spe
    self.suggestion_id = 1

  @property
  def is_initialization_phase(self):
    minimum_num_initial_observations = max(2 * self.experiment.dimension, 4)
    num_valid_observations = sum(1 for o in self.observations if not o.failed)
    return num_valid_observations <= minimum_num_initial_observations

  @property
  def use_random(self):
    return self.experiment.is_random or self.is_initialization_phase

  @property
  def use_spe(self):
    if (
      self.experiment.dimension > DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS
      or len(self.observations) > DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS
      or self.force_spe
    ):
      return True
    return False

  @property
  def experiment_progress_dict(self):
    observation_count = len(self.observations)
    observation_budget_consumed = observation_count
    if self.experiment.is_multitask:
      observation_budget_consumed = sum([o.task.cost for o in self.observations])

    return dict(
      observation_budget_consumed=observation_budget_consumed,
      observation_count=observation_count,
    )

  def create_observation(self, assignments=None, values=None, suggestion=None, failed=False, task=None):
    if not (bool(not assignments) ^ bool(not suggestion)):
      raise LocalBadParamError("Need to pass in an assignments dictionary or a suggestion id to create an observation")

    if assignments is None:
      if self.stored_suggestion is None:
        raise LocalBadParamError("There is no stored suggestion to use. Please create a suggestion")

      if suggestion != self.stored_suggestion.id:
        raise LocalBadParamError(
          f"The suggestion you provided: {suggestion} does not match the suggestion stored: {self.stored_suggestion.id}"
        )

      assignments = self.stored_suggestion.assignments
      if self.stored_suggestion.task is not None:
        task = dataclass_to_dict(self.stored_suggestion.task)

    observation = LocalObservationBuilder(
      input_dict=dict(
        assignments=assignments,
        values=values,
        failed=failed,
        task=task,
      ),
      experiment=self.experiment,
    )
    self.observations.append(observation)
    self.stored_suggestion = None
    return observation.get_client_observation(self.experiment)

  def get_observations(self):
    return [o.get_client_observation(self.experiment) for o in self.observations]

  def create_suggestion(self):
    if self.stored_suggestion is not None:
      return self.stored_suggestion

    if self.use_random:
      source = RandomSearchSource(self.experiment)
    elif self.use_spe:
      source = SPESource(self.experiment)
    else:
      source = GPSource(self.experiment)
      self.hyperparameters = source.update_hyperparameters(self.observations, self.hyperparameters)
    suggestion_data = source.get_suggestion(self.observations)

    suggestion_to_serve = LocalSuggestion(
      id=str(self.suggestion_id),
      assignments=suggestion_data.assignments,
      task=suggestion_data.task,
    )
    self.stored_suggestion = suggestion_to_serve
    self.suggestion_id += 1
    return suggestion_to_serve
