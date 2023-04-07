# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.experiment.model import Experiment
from zigopt.json.assignments import assignments_json
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.task import TaskJsonBuilder
from zigopt.queued_suggestion.model import QueuedSuggestion


class QueuedSuggestionJsonBuilder(JsonBuilder):
  object_name = "queued_suggestion"

  def __init__(self, experiment: Experiment, queued_suggestion: QueuedSuggestion):
    assert experiment.id == queued_suggestion.experiment_id
    self._experiment = experiment
    self._queued_suggestion = queued_suggestion

  @field(ValidationType.object)
  def assignments(self) -> dict[str, int | float | str | None]:
    return assignments_json(self._experiment, self._queued_suggestion.get_assignments(self._experiment))

  @field(ValidationType.integer)
  def created(self) -> int:
    return self._queued_suggestion.created_time

  @field(ValidationType.id)
  def experiment(self) -> int:
    return self._experiment.id

  @field(ValidationType.id)
  def id(self) -> int:
    return self._queued_suggestion.id

  def hide_task(self):
    return not self._experiment.is_multitask

  @field(JsonBuilderValidationType(), hide=hide_task)
  def task(self) -> Optional[TaskJsonBuilder]:
    return napply(self._queued_suggestion.task, TaskJsonBuilder)
