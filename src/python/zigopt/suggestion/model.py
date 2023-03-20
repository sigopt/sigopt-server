# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class Suggestion(object):
  def __init__(self, processed=None, unprocessed=None, observation=None):
    assert unprocessed is not None, "Suggestion needs an UnprocessedSuggestion"
    self._processed = processed
    self._unprocessed = unprocessed
    self._observation = observation

  def set_observation(self, observation=None):
    self._observation = observation

  @property
  def state(self):
    return "open" if self._observation is None else "closed"

  @property
  def processed(self):
    return self._processed

  @property
  def unprocessed(self):
    return self._unprocessed

  @property
  def observation(self):
    return self._observation

  @property
  def id(self):
    return self._processed and self._processed.suggestion_id

  @property
  def suggestion_meta(self):
    return self._unprocessed and self._unprocessed.suggestion_meta

  @property
  def source(self):
    return self._unprocessed and self._unprocessed.source

  @property
  def created(self):
    return self._processed and self._processed.processed_time

  @property
  def experiment_id(self):
    return self._processed and self._processed.experiment_id

  @property
  def deleted(self):
    return self._processed and self._processed.deleted

  @property
  def task(self):
    return self._unprocessed and self._unprocessed.task

  @property
  def automatic(self):
    return self._processed and self._processed.automatic

  @property
  def client_provided_data(self):
    return self._processed and self._processed.client_provided_data

  def get_assignments(self, experiment):
    if self._processed and experiment.id != self._processed.experiment_id:
      raise Exception(
        f"Experiment id {experiment.id} does not match processed Suggestion id {self._processed.experiment_id}"
      )

    return self._unprocessed.get_assignments(experiment)

  def get_assignment(self, parameter):
    return self._unprocessed.get_assignment(parameter)

  def assignments(self, experiment):
    return self.unprocessed.get_assignments(experiment)

  def get_conditional_assignments(self, experiment):
    return self.unprocessed.get_conditional_assignments(experiment)
