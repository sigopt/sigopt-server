# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *


class OptimizationArgs:
  def __init__(
    self,
    source,
    observation_iterator,
    observation_count,
    failure_count,
    max_observation_id,
    old_hyperparameters,
    open_suggestions,
    last_observation,
  ):
    self._source = source
    self._observation_count = observation_count
    self._failure_count = failure_count
    self._old_hyperparameters = old_hyperparameters
    self._open_suggestions = open_suggestions
    self._max_observation_id = max_observation_id
    self._observation_iter = safe_iterator(observation_iterator)
    self._last_observation = last_observation

  @property
  def observation_iterator(self):
    return self._observation_iter

  @property
  def source(self):
    return self._source

  @property
  def observation_count(self):
    return self._observation_count

  @property
  def failure_count(self):
    return self._failure_count

  @property
  def open_suggestions(self):
    return self._open_suggestions

  @property
  def old_hyperparameters(self):
    return self._old_hyperparameters

  @property
  def max_observation_id(self):
    return self._max_observation_id

  @property
  def last_observation(self):
    return self._last_observation

  def copy_and_set(
    self,
    source=None,
    observation_iterator=None,
    observation_count=None,
    failure_count=None,
    max_observation_id=None,
    old_hyperparameters=None,
    open_suggestions=None,
    last_observation=None,
  ):
    return OptimizationArgs(
      source=coalesce(source, self.source),
      observation_iterator=coalesce(observation_iterator, self.observation_iterator),
      observation_count=coalesce(observation_count, self.observation_count),
      failure_count=coalesce(failure_count, self.failure_count),
      max_observation_id=coalesce(max_observation_id, self.max_observation_id),
      old_hyperparameters=old_hyperparameters or self.old_hyperparameters,
      open_suggestions=coalesce(open_suggestions, self.open_suggestions),
      last_observation=coalesce(last_observation, self.last_observation),
    )
