# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import Task  # type: ignore


class TaskJsonBuilder(JsonBuilder):
  object_name = "task"

  def __init__(self, task: Task):
    assert isinstance(task, Task)
    self._task = task

  @field(ValidationType.string)
  def name(self) -> str:
    return self._task.name

  @field(ValidationType.number)
  def cost(self) -> float:
    return self._task.cost
