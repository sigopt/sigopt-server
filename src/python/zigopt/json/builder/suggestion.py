# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.experiment.model import Experiment
from zigopt.json.assignments import assignments_json
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.task import TaskJsonBuilder
from zigopt.json.client_provided_data import client_provided_data_json
from zigopt.suggestion.model import Suggestion


class SuggestionJsonBuilder(JsonBuilder):
  object_name = "suggestion"

  def __init__(self, experiment: Experiment, suggestion: Suggestion, auth: EmptyAuthorization):
    assert isinstance(suggestion, Suggestion)
    self._experiment = experiment
    self._suggestion = suggestion
    self._auth = auth

  @field(ValidationType.object)
  def assignments(self) -> dict[str, int | float | str | None]:
    return assignments_json(self._experiment, self._suggestion.get_assignments(self._experiment))

  @field(ValidationType.integer)
  def created(self) -> int:
    return self._suggestion.created

  @field(ValidationType.boolean)
  def deleted(self) -> bool:
    return self._suggestion.deleted

  @field(ValidationType.id)
  def experiment(self) -> int:
    return self._experiment.id

  @field(ValidationType.id)
  def id(self) -> int:
    return self._suggestion.id or self._suggestion.unprocessed.id

  @field(ValidationType.object)
  def metadata(self) -> Optional[dict[str, int | float | str]]:
    return client_provided_data_json(self._suggestion.client_provided_data)

  @field(ValidationType.string)
  def state(self) -> str:
    return self._suggestion.state

  def hide_task(self):
    return not self._experiment.is_multitask

  @field(JsonBuilderValidationType(), hide=hide_task)
  def task(self) -> Optional[TaskJsonBuilder]:
    return napply(self._suggestion.task, TaskJsonBuilder)
