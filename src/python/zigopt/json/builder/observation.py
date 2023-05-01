# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from numpy import sqrt

from zigopt.common import *
from zigopt.experiment.model import Experiment
from zigopt.json.assignments import assignments_json
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.task import TaskJsonBuilder
from zigopt.json.client_provided_data import client_provided_data_json
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationValue


class BaseValueJsonBuilder(JsonBuilder):
  def __init__(self, value: ObservationValue):
    self._value = value

  def name(self):
    raise NotImplementedError()

  @field(ValidationType.number)
  def value(self) -> Optional[float]:
    if self._value.HasField("value"):
      return self._value.value
    return None

  @field(ValidationType.number)
  def value_stddev(self) -> Optional[float]:
    if self._value.HasField("value_var"):
      return sqrt(self._value.value_var)
    return None


class ValueJsonBuilder(BaseValueJsonBuilder):
  object_name = "metric_evaluation"

  @field(ValidationType.string)
  def name(self) -> Optional[str]:
    if self._value.HasField("name"):
      return self._value.name
    return None


class ObservationDataJsonBuilder(JsonBuilder):
  def __init__(self, experiment: Experiment, observation: Observation):
    self._experiment = experiment
    self._observation = observation

  @field(ValidationType.object)
  def assignments(self) -> dict[str, int | float | str | None]:
    return assignments_json(self._experiment, self._observation.get_assignments(self._experiment))

  @field(ValidationType.id)
  def id(self) -> int:
    return self._observation.id

  @field(ValidationType.object)
  def metadata(self) -> Optional[dict[str, int | float | str]]:
    return client_provided_data_json(self._observation.client_provided_data)

  def hide_task(self):
    return not self._experiment.is_multitask

  @field(ValidationType.string, hide=hide_task)
  def task(self) -> str:
    return self._observation.task.name

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def values(self) -> list[ValueJsonBuilder]:
    return [ValueJsonBuilder(value) for value in self._observation.get_all_measurements(self._experiment)]


class ObservationJsonBuilder(ObservationDataJsonBuilder):
  object_name = "observation"

  @field(ValidationType.integer)
  def created(self) -> int:
    return self._observation.timestamp

  @field(ValidationType.id)
  def experiment(self) -> int:
    return self._experiment.id

  @field(ValidationType.boolean)
  def failed(self) -> bool:
    return self._observation.reported_failure

  @field(ValidationType.id)
  def suggestion(self) -> Optional[int]:
    return self._observation.processed_suggestion_id

  def hide_task(self):
    return not self._experiment.is_multitask

  @field(JsonBuilderValidationType(), hide=hide_task)
  def task(self) -> Optional[TaskJsonBuilder]:
    return napply(self._observation.task, TaskJsonBuilder)
