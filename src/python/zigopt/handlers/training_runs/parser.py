# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.validate.base import validate_name
from zigopt.handlers.validate.metadata import validate_metadata
from zigopt.handlers.validate.sys_metadata import validate_sys_metadata
from zigopt.handlers.validate.training_run import (
  validate_assignments_meta_json,
  validate_assignments_sources_json,
  validate_state,
)
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.protobuf.dict import dict_to_protobuf, dict_to_protobuf_struct, protobuf_struct_to_dict, protobuf_to_dict
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import (
  AssignmentsRunMeta,
  AssignmentsSources,
  Dataset,
  Log,
  SourceCode,
  SysMetadata,
  TrainingRunData,
  TrainingRunModel,
  TrainingRunValue,
)


EXPLICITLY_NULL = object()
# NOTE: 100 is ~length of the disclaimer that the python client adds
MAX_LOG_LENGTH = 1024 + 100


# This class is used to validate that JSON represents a valid protobuf as we
# build it, while still retaining that JSON. This is so we can keep track of
# which fields were set as None, which is not natively tracked by a protobuf object.
class ProtobufBuilderThatRetainsNones:
  def __init__(self, Cls):
    self.Cls = Cls
    self._builder = {}

  def add_field(self, k, v):
    json_value = v
    self._builder[self.Cls.DESCRIPTOR.fields_by_name[k].json_name] = json_value

  @property
  def json(self):
    def unbuild(builder):
      return builder.json if isinstance(builder, ProtobufBuilderThatRetainsNones) else builder

    return recursively_map_dict(unbuild, self._builder)

  @property
  def protobuf(self):
    return dict_to_protobuf(self.Cls, self.json)


class TrainingRunRequestParams:
  valid_fields = (
    "assignments",
    "assignments_meta",
    "assignments_sources",
    "datasets",
    "deleted",
    "favorite",
    "logs",
    "metadata",
    "model",
    "name",
    "project",
    "source_code",
    "state",
    "values",
    "sys_metadata",
    "dev_metadata",
  )

  def __init__(self, deleted, project, training_run_data_json, training_run_data):
    self._deleted = deleted
    self._project = project
    self.training_run_data_json = training_run_data_json
    self.training_run_data = training_run_data

  @property
  def deleted(self):
    return False if self._deleted is EXPLICITLY_NULL else self._deleted

  @property
  def project(self):
    return None if self._project is EXPLICITLY_NULL else self._project

  def field_is_explicitly_null(self, protobuf_name):
    if protobuf_name in ("project"):
      return getattr(self, f"_{protobuf_name}") is EXPLICITLY_NULL
    json_name = TrainingRunData.DESCRIPTOR.fields_by_name[protobuf_name].json_name
    return self.training_run_data_json.get(json_name, object()) is None


class TrainingRunRequestParser:
  @generator_to_dict
  def parse_datasets(self, datasets):
    if datasets is None:
      return
    for name in datasets:
      dataset = ProtobufBuilderThatRetainsNones(Dataset)
      yield (name, dataset)

  @generator_to_dict
  def parse_logs(self, logs):
    if logs is None:
      return
    for typ, log_dict in logs.items():
      log = ProtobufBuilderThatRetainsNones(Log)
      content = get_with_validation(log_dict, "content", ValidationType.string)
      if content and len(content) > MAX_LOG_LENGTH:
        content = content[:MAX_LOG_LENGTH]
      log.add_field("content", content)
      yield (typ, log)

  def parse_source_code(self, code_dict):
    if code_dict is None:
      return None
    source_code = ProtobufBuilderThatRetainsNones(SourceCode)
    source_code.add_field("content", get_opt_with_validation(code_dict, "content", ValidationType.string))
    source_code.add_field("hash", get_opt_with_validation(code_dict, "hash", ValidationType.string))
    return source_code

  @generator_to_dict
  def parse_values(self, values_dict):
    if values_dict is None:
      return
    for name, value_dict in values_dict.items():
      value = ProtobufBuilderThatRetainsNones(TrainingRunValue())
      value.add_field("value", get_with_validation(value_dict, "value", ValidationType.number))
      value_stddev = get_opt_with_validation(value_dict, "value_stddev", ValidationType.number)
      value.add_field("value_var", napply(value_stddev, lambda x: x * x))
      yield (name, value)

  @generator_to_dict
  def parse_assignments_meta(self, assignments_meta):
    if assignments_meta is None:
      return
    validate_assignments_meta_json(assignments_meta)
    for a_name, a_meta_json in assignments_meta.items():
      a_meta = ProtobufBuilderThatRetainsNones(AssignmentsRunMeta())
      a_meta.add_field("source", get_with_validation(a_meta_json, "source", ValidationType.string))
      yield (a_name, a_meta)

  @generator_to_dict
  def parse_assignments_sources(self, assignments_sources):
    if assignments_sources is None:
      return
    validate_assignments_sources_json(assignments_sources)
    for name, source_json in assignments_sources.items():
      source = ProtobufBuilderThatRetainsNones(AssignmentsSources())
      source.add_field("default_show", get_with_validation(source_json, "default_show", ValidationType.boolean))
      source.add_field("sort", get_with_validation(source_json, "sort", ValidationType.number))
      yield (name, source)

  def parse_state(self, state_string):
    return validate_state(state_string)

  def parse_training_run_model(self, model_dict):
    training_run_model = ProtobufBuilderThatRetainsNones(TrainingRunModel)
    training_run_model.add_field("type", get_opt_with_validation(model_dict, "type", ValidationType.string))
    return training_run_model

  def parse_name(self, name):
    return validate_name(name)

  def parse_metadata(self, metadata):
    if metadata is None:
      metadata = dict_to_protobuf_struct({})
    return protobuf_struct_to_dict(validate_metadata(metadata))

  def parse_sys_metadata(self, metadata):
    if metadata is None:
      return SysMetadata()
    return protobuf_to_dict(validate_sys_metadata(metadata))

  def get_opt_or_explicitly_null(self, params, key, validation_type):
    if key in params:
      return coalesce(get_opt_with_validation(params, key, validation_type), EXPLICITLY_NULL)
    return None

  def parse_params(self, request):
    training_run_data = ProtobufBuilderThatRetainsNones(TrainingRunData)

    params = request.params()
    project = self.get_opt_or_explicitly_null(params, "project", ValidationType.id_string)
    deleted = self.get_opt_or_explicitly_null(params, "deleted", ValidationType.boolean)

    for protobuf_name, user_name, validation_type, parser in (
      ("assignments_struct", "assignments", ValidationType.metadata, self.parse_metadata),
      (
        "assignments_meta",
        "assignments_meta",
        ValidationType.objectOf(ValidationType.object),
        self.parse_assignments_meta,
      ),
      (
        "assignments_sources",
        "assignments_sources",
        ValidationType.objectOf(ValidationType.object),
        self.parse_assignments_sources,
      ),
      ("datasets", "datasets", ValidationType.objectOf(ValidationType.object), self.parse_datasets),
      ("favorite", "favorite", ValidationType.boolean, lambda x: x),
      ("logs", "logs", ValidationType.objectOf(ValidationType.object), self.parse_logs),
      ("metadata", "metadata", ValidationType.metadata, self.parse_metadata),
      ("dev_metadata", "dev_metadata", ValidationType.metadata, self.parse_metadata),
      ("sys_metadata", "sys_metadata", ValidationType.sys_metadata, self.parse_sys_metadata),
      ("training_run_model", "model", ValidationType.object, self.parse_training_run_model),
      ("name", "name", ValidationType.string, self.parse_name),
      ("source_code", "source_code", ValidationType.object, self.parse_source_code),
      ("state", "state", ValidationType.string, self.parse_state),
      ("values_map", "values", ValidationType.objectOf(ValidationType.object), self.parse_values),
    ):
      if user_name in params:
        protobuf_value = napply(get_opt_with_validation(params, user_name, validation_type), parser)
        training_run_data.add_field(protobuf_name, protobuf_value)
    return TrainingRunRequestParams(
      deleted=deleted,
      project=project,
      training_run_data_json=training_run_data.json,
      # NOTE: We could omit this since it's not always used
      # (specifically, the update handler does not require it).
      # However, it provides a good sanity check that the JSON creates a valid protobuf before proceeding
      training_run_data=training_run_data.protobuf,
    )
