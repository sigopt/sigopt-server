# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Iterator, Sequence

from zigopt.common import *
from zigopt.observation.model import Observation
from zigopt.optimization_aux.service import Hyperparams
from zigopt.optimize.sources.base import OptimizationSource
from zigopt.suggestion.model import Suggestion


class OptimizationArgs:  # pylint: disable=too-many-instance-attributes
  def __init__(
    self,
    source: OptimizationSource,
    observation_iterator: Iterator[Observation],
    observation_count: int,
    failure_count: int,
    max_observation_id: int | None,
    old_hyperparameters: Hyperparams | None,
    open_suggestions: Sequence[Suggestion],
    last_observation: Observation | None,
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
  def observation_iterator(self) -> Iterator[Observation]:
    return self._observation_iter

  @property
  def source(self) -> OptimizationSource:
    return self._source

  @property
  def observation_count(self) -> int:
    return self._observation_count

  @property
  def failure_count(self) -> int:
    return self._failure_count

  @property
  def open_suggestions(self) -> Sequence[Suggestion]:
    return self._open_suggestions

  @property
  def old_hyperparameters(self) -> Hyperparams | None:
    return self._old_hyperparameters

  @property
  def max_observation_id(self) -> int | None:
    return self._max_observation_id

  @property
  def last_observation(self) -> Observation | None:
    return self._last_observation

  def copy_and_set(
    self,
    source: OptimizationSource | None = None,
    observation_iterator: Iterator[Observation] | None = None,
    observation_count: int | None = None,
    failure_count: int | None = None,
    max_observation_id: int | None = None,
    old_hyperparameters: Hyperparams | None = None,
    open_suggestions: Sequence[Suggestion] | None = None,
    last_observation: Observation | None = None,
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
