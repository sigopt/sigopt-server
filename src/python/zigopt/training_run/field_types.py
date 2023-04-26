# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from enum import Enum

from zigopt.common import *
from zigopt.pagination.lib import FieldApiType
from zigopt.training_run.model import TrainingRun


class FieldType(Enum):
  primitive = 1
  protobuf_primitive = 2
  protobuf_struct = 3
  protobuf_object = 4
  protobuf_map_of_object = 5


class FieldDetails:
  type: FieldType

  def __init__(self, api_name, column_accessor, api_type, readable_name=None, sortable=False):
    self.api_name = api_name
    self.readable_name = readable_name
    self.column_accessor = column_accessor
    self.api_type = api_type
    self.sortable = sortable

  @property
  def json_name(self):
    raise NotImplementedError()


class PrimitiveFieldDetails(FieldDetails):
  type = FieldType.primitive

  @property
  def sql_accessor(self):
    return self.column_accessor


class BaseProtobufFieldDetails(FieldDetails):
  def __init__(self, *args, protobuf_field_name, **kwargs):
    super().__init__(*args, **kwargs)
    self.protobuf_class = self.column_accessor.protobuf_class
    self.protobuf_field_name = protobuf_field_name

  @property
  def json_name(self):
    return self.protobuf_class.DESCRIPTOR.fields_by_name[self.protobuf_field_name].json_name

  @property
  def sql_accessor(self):
    return self.column_accessor[self.json_name]


class ProtobufPrimitiveFieldDetails(BaseProtobufFieldDetails):
  type = FieldType.protobuf_primitive


class BaseNestedProtobufFieldDetails(BaseProtobufFieldDetails):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._nested_field = self.protobuf_class.DESCRIPTOR.fields_by_name[self.protobuf_field_name]


class ProtobufStructFieldDetails(BaseNestedProtobufFieldDetails):
  type = FieldType.protobuf_struct


class ProtobufObjectFieldDetails(BaseNestedProtobufFieldDetails):
  type = FieldType.protobuf_object

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._enclosed_object_json_to_api_mapping = {
      nested_subfield.json_name: nested_subfield for nested_subfield in self._nested_field.message_type.fields
    }

  @property
  def all_json_keys(self):
    return list(self._enclosed_object_json_to_api_mapping.keys())

  def get_enclosed_sub_field_by_json_name(self, json_name):
    return self._enclosed_object_json_to_api_mapping.get(json_name)


class ProtobufMapFieldDetails(BaseNestedProtobufFieldDetails):
  type = FieldType.protobuf_map_of_object

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._enclosed_object_json_to_api_mapping = {
      nested_subfield.json_name: nested_subfield
      for nested_subfield in self._nested_field.message_type.fields_by_name["value"].message_type.fields
    }

  @property
  def all_json_keys(self):
    return list(self._enclosed_object_json_to_api_mapping.keys())

  def get_enclosed_sub_field_by_json_name(self, json_name):
    return self._enclosed_object_json_to_api_mapping.get(json_name)


TRAINING_RUN_API_FIELDS = [
  # Primitive fields that correspond to a column in the database
  PrimitiveFieldDetails("id", TrainingRun.id, FieldApiType.id, sortable=True, readable_name="ID"),
  PrimitiveFieldDetails(
    "experiment",
    TrainingRun.experiment_id,
    FieldApiType.id,
    sortable=True,
    readable_name="Experiment",
  ),
  # NOTE: Project and client are excluded, since they will always be the same.
  # PrimitiveFieldDetails('client', TrainingRun.client_id, FieldApiType.id, readable_name='Client', sortable=True),
  # PrimitiveFieldDetails('project', TrainingRun.project_id, FieldApiType.id, readable_name='Project'),
  PrimitiveFieldDetails(
    "suggestion",
    TrainingRun.suggestion_id,
    FieldApiType.id,
    sortable=True,
    readable_name="Suggestion",
  ),
  PrimitiveFieldDetails(
    "observation",
    TrainingRun.observation_id,
    FieldApiType.id,
    sortable=True,
    readable_name="Observation",
  ),
  PrimitiveFieldDetails(
    "user",
    TrainingRun.created_by,
    FieldApiType.id,
    sortable=True,
    readable_name="Created By",
  ),
  PrimitiveFieldDetails(
    "created",
    TrainingRun.created,
    FieldApiType.timestamp,
    sortable=True,
    readable_name="Created",
  ),
  PrimitiveFieldDetails(
    "updated",
    TrainingRun.updated,
    FieldApiType.timestamp,
    sortable=True,
    readable_name="Updated",
  ),
  PrimitiveFieldDetails(
    "completed",
    TrainingRun.completed,
    FieldApiType.timestamp,
    sortable=True,
    readable_name="Completed",
  ),
  PrimitiveFieldDetails(
    "deleted",
    TrainingRun.deleted,
    FieldApiType.boolean,
    sortable=True,
    readable_name="Archived",
  ),
  # Primitive fields that correspond to a top-level protobuf field
  ProtobufPrimitiveFieldDetails(
    "name",
    TrainingRun.training_run_data,
    FieldApiType.string,
    sortable=True,
    protobuf_field_name="name",
    readable_name="Name",
  ),
  ProtobufPrimitiveFieldDetails(
    "favorite",
    TrainingRun.training_run_data,
    FieldApiType.boolean,
    sortable=True,
    protobuf_field_name="favorite",
    readable_name="Favorite",
  ),
  # Protobuf struct fields
  ProtobufStructFieldDetails(
    "assignments",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="assignments_struct",
  ),
  ProtobufStructFieldDetails(
    "metadata",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="metadata",
  ),
  # Protobuf object fields
  ProtobufObjectFieldDetails(
    "source_code",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="source_code",
  ),
  ProtobufObjectFieldDetails(
    "model",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="training_run_model",
  ),
  # Protobuf map fields
  ProtobufMapFieldDetails(
    "datasets",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="datasets",
  ),
  ProtobufMapFieldDetails(
    "logs",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="logs",
  ),
  ProtobufMapFieldDetails(
    "values",
    TrainingRun.training_run_data,
    FieldApiType.object,
    sortable=True,
    protobuf_field_name="values_map",
  ),
]
