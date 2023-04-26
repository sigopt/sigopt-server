# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional, Sequence

from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module

from zigopt.common import *
from zigopt.checkpoint.model import Checkpoint
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.observation import ValueJsonBuilder


class CheckpointJsonBuilder(JsonBuilder):
  object_name = "checkpoint"

  def __init__(self, checkpoint: Checkpoint):
    self._checkpoint: Checkpoint = checkpoint

  @field(ValidationType.id)
  def id(self) -> int:
    return self._checkpoint.id

  @field(ValidationType.id)
  def training_run(self) -> int:
    return self._checkpoint.training_run_id

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._checkpoint.created, datetime_to_seconds)

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def values(self) -> Sequence[ValueJsonBuilder]:
    return [ValueJsonBuilder(measurement) for measurement in self._checkpoint.sorted_measurements()]

  @field(ValidationType.metadata)
  def metadata(self) -> Optional[Struct]:
    return self._checkpoint.data.metadata if self._checkpoint.data.HasField("metadata") else None
