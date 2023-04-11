# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module

from zigopt.common import *
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.project.model import Project


class ProjectJsonBuilder(JsonBuilder):
  object_name = "project"

  def __init__(self, project: Project, experiment_count: int, training_run_count: int):
    self._project = project
    self._experiment_count = experiment_count
    self._training_run_count = training_run_count

  @field(ValidationType.string)
  def id(self) -> int:
    return self._project.reference_id

  @field(ValidationType.string)
  def name(self) -> str:
    return self._project.name

  @field(ValidationType.id)
  def client(self) -> int:
    return self._project.client_id

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._project.created_by

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._project.date_created, datetime_to_seconds)

  @field(ValidationType.integer)
  def updated(self) -> Optional[float]:
    return napply(self._project.date_updated, datetime_to_seconds)

  @field(ValidationType.metadata)
  def metadata(self) -> Optional[Struct]:
    return self._project.data.GetFieldOrNone("metadata")

  @field(ValidationType.integer)
  def experiment_count(self) -> int:
    return self._experiment_count

  @field(ValidationType.integer)
  def training_run_count(self) -> int:
    return self._training_run_count

  @field(ValidationType.boolean)
  def deleted(self) -> bool:
    return self._project.deleted
