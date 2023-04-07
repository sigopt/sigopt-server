# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module

from zigopt.common import *
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.observation import BaseValueJsonBuilder
from zigopt.project.model import Project
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationValue
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import (
  AssignmentsRunMeta,
  AssignmentsSources,
  Dataset,
  Log,
  SourceCode,
  SysMetadata,
  TrainingRunModel,
)
from zigopt.training_run.constant import TRAINING_RUN_STATE_TO_JSON
from zigopt.training_run.model import TrainingRun


class TrainingRunValueJsonBuilder(BaseValueJsonBuilder):
  object_name = "metric_evaluation"

  def __init__(self, value: ObservationValue, name: str):
    super().__init__(value=value)
    self._name = name

  @field(ValidationType.string)
  def name(self) -> str:
    return self._name


# Note: map<SOURCE_NAME, AssignmentsSources> - this is metadata about the source
class TrainingRunAssignmentsSourcesJsonBuilder(JsonBuilder):
  object_name = "assignments_sources"

  def __init__(self, source: AssignmentsSources):
    self._source = source

  @field(ValidationType.boolean)
  def default_show(self) -> bool:
    return self._source.default_show

  @field(ValidationType.number)
  def sort(self) -> int:
    return self._source.sort


class TrainingRunAssignmentsMetaJsonBuilder(JsonBuilder):
  object_name = "assignments_meta"

  def __init__(self, a_meta: AssignmentsRunMeta):
    self._a_meta = a_meta

  @field(ValidationType.string)
  def source(self) -> str:
    return self._a_meta.source


class DatasetJsonBuilder(JsonBuilder):
  object_name = "dataset"

  def __init__(self, dataset: Dataset):
    super().__init__()


class LogJsonBuilder(JsonBuilder):
  object_name = "log"

  def __init__(self, log: Log):
    self._log = log

  @field(ValidationType.string)
  def content(self) -> Optional[str]:
    return self._log.GetFieldOrNone("content")


class TrainingRunModelJsonBuilder(JsonBuilder):
  object_name = "model"

  def __init__(self, training_run_model: TrainingRunModel):
    self._training_run_model = training_run_model

  @field(ValidationType.string)
  def type(self) -> Optional[str]:
    return self._training_run_model.GetFieldOrNone("type")


class SourceCodeJsonBuilder(JsonBuilder):
  object_name = "source_code"

  def __init__(self, source_code: SourceCode):
    self._source_code = source_code

  @field(ValidationType.string)
  def content(self) -> Optional[str]:
    return self._source_code.GetFieldOrNone("content")

  @field(ValidationType.string)
  def hash(self) -> Optional[str]:
    return self._source_code.GetFieldOrNone("hash")


# TODO(SN-1112): Only used in MPM endpoints for now, can port over to
# existing training run endpoints after content is backfilled
class TrainingRunJsonBuilder(JsonBuilder):
  object_name = "training_run"

  def __init__(self, training_run: TrainingRun, checkpoint_count: int, project: Project):
    self._training_run = training_run
    self._checkpoint_count = checkpoint_count
    self._project: Project = project

  @field(ValidationType.id)
  def id(self) -> int:
    return self._training_run.id

  @field(ValidationType.id)
  def suggestion(self) -> Optional[int]:
    return self._training_run.suggestion_id

  @field(ValidationType.id)
  def observation(self) -> Optional[int]:
    return self._training_run.observation_id

  @field(ValidationType.boolean)
  def finished(self) -> bool:
    return bool(self._training_run.observation_id or self._training_run.completed)

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._training_run.created, datetime_to_seconds)

  @field(ValidationType.integer)
  def updated(self) -> Optional[float]:
    return napply(self._training_run.updated, datetime_to_seconds)

  @field(ValidationType.integer)
  def checkpoint_count(self) -> int:
    return self._checkpoint_count

  @field(ValidationType.metadata)
  def metadata(self) -> Optional[Struct]:
    return self._training_run.training_run_data.GetFieldOrNone("metadata")

  @field(ValidationType.metadata)
  def dev_metadata(self) -> Optional[Struct]:
    return self._training_run.training_run_data.dev_metadata

  @field(ValidationType.boolean)
  def favorite(self) -> bool:
    return self._training_run.training_run_data.favorite

  @field(ValidationType.sys_metadata)
  def sys_metadata(self) -> Optional[SysMetadata]:
    return self._training_run.training_run_data.sys_metadata

  @field(ValidationType.metadata)
  def assignments(self) -> Struct:
    return self._training_run.training_run_data.assignments_struct

  @field(ValidationType.objectOf(JsonBuilderValidationType()))
  def assignments_meta(self) -> dict[str, TrainingRunAssignmentsMetaJsonBuilder]:
    meta = {
      a_name: TrainingRunAssignmentsMetaJsonBuilder(a_meta)
      for a_name, a_meta in self._training_run.training_run_data.assignments_meta.items()
    }
    return meta

  @field(ValidationType.objectOf(JsonBuilderValidationType()))
  def assignments_sources(self) -> dict[str, TrainingRunAssignmentsSourcesJsonBuilder]:
    return {
      source_name: TrainingRunAssignmentsSourcesJsonBuilder(source)
      for source_name, source in self._training_run.training_run_data.assignments_sources.items()
    }

  @field(ValidationType.id)
  def client(self) -> int:
    return self._training_run.client_id

  @field(ValidationType.integer)
  def completed(self) -> Optional[float]:
    return napply(self._training_run.completed, datetime_to_seconds)

  @field(ValidationType.boolean)
  def deleted(self) -> bool:
    return bool(self._training_run.deleted)

  @field(ValidationType.objectOf(JsonBuilderValidationType()))
  def datasets(self) -> dict[str, DatasetJsonBuilder]:
    return map_dict(DatasetJsonBuilder, self._training_run.training_run_data.datasets)

  @field(ValidationType.id)
  def experiment(self) -> int:
    return self._training_run.experiment_id

  @field(ValidationType.objectOf(JsonBuilderValidationType()))
  def logs(self) -> dict[str, LogJsonBuilder]:
    return map_dict(LogJsonBuilder, self._training_run.training_run_data.logs)

  @field(JsonBuilderValidationType())
  def model(self) -> TrainingRunModelJsonBuilder:
    return TrainingRunModelJsonBuilder(self._training_run.training_run_data.training_run_model)

  @field(ValidationType.string)
  def name(self) -> Optional[str]:
    return self._training_run.training_run_data.GetFieldOrNone("name")

  @field(ValidationType.id_string)
  def project(self) -> Optional[str]:
    return napply(self._project, lambda p: p.reference_id)

  @field(JsonBuilderValidationType())
  def source_code(self) -> SourceCodeJsonBuilder:
    return SourceCodeJsonBuilder(self._training_run.training_run_data.source_code)

  @field(ValidationType.string)
  def state(self) -> str:
    return TRAINING_RUN_STATE_TO_JSON[self._training_run.state]

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._training_run.created_by

  @field(ValidationType.objectOf(JsonBuilderValidationType()))
  def values(self) -> dict[str, TrainingRunValueJsonBuilder]:
    return {
      name: TrainingRunValueJsonBuilder(value, name=name)
      for name, value in self._training_run.training_run_data.values_map.items()
    }

  @field(ValidationType.arrayOf(ValidationType.id))
  def tags(self) -> list[int]:
    return list(self._training_run.training_run_data.tags.keys())

  @field(ValidationType.arrayOf(ValidationType.id))
  def files(self) -> list[int]:
    return sorted(self._training_run.training_run_data.files.keys())
