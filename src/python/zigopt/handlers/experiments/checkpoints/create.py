# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module

from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.checkpoint.model import CHECKPOINT_MAX_METADATA_FIELDS, Checkpoint
from zigopt.common.numbers import *
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.handlers.validate.checkpoint import validate_checkpoint_json_dict_for_create
from zigopt.handlers.validate.metadata import validate_metadata
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import CheckpointJsonBuilder
from zigopt.net.errors import ForbiddenError
from zigopt.observation.data import validate_metric_names
from zigopt.protobuf.gen.checkpoint.checkpoint_data_pb2 import CheckpointData
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationValue
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from libsigopt.aux.errors import SigoptValidationError


class CheckpointsCreateHandler(TrainingRunHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct(
    "Params",
    [
      "values",
      "metadata",
    ],
  )

  @generator_to_list
  def _parse_values(self, data):
    values = get_with_validation(data, "values", ValidationType.arrayOf(ValidationType.object))
    validate_metric_names(values, self.experiment)
    for value_dict in values:
      observation_value = ObservationValue()
      observation_value.name = get_with_validation(value_dict, "name", ValidationType.string)
      observation_value.value = get_with_validation(value_dict, "value", ValidationType.number)
      value_stddev: float | None = get_opt_with_validation(value_dict, "value_stddev", ValidationType.number)
      value_var = napply(value_stddev, lambda stddev: stddev * stddev)
      if value_var is not None:
        observation_value.value_var = value_var
      yield observation_value

  def parse_params(self, request):
    data = request.params()
    validate_checkpoint_json_dict_for_create(data)
    values = self._parse_values(data)
    metadata: Struct | None = get_opt_with_validation(data, "metadata", ValidationType.metadata)
    return self.Params(
      values=values,
      metadata=napply(
        metadata,
        lambda obj: validate_metadata(obj, max_keys=CHECKPOINT_MAX_METADATA_FIELDS),
      ),
    )

  def handle(self, params):  # type: ignore
    assert self.training_run is not None

    if self.experiment and self.experiment.deleted:
      raise SigoptValidationError(f"Cannot create checkpoints for deleted experiment {self.experiment.id}")

    checkpoints = self.services.checkpoint_service.find_by_training_run_id(self.training_run.id)
    max_checkpoints = self._get_max_checkpoints(self.experiment)
    if len(checkpoints) >= max_checkpoints:
      raise ForbiddenError(f"Training run {self.training_run.id} cannot exceed {max_checkpoints} checkpoints.")

    if self.training_run.observation_id:
      raise ForbiddenError(
        f"Training run {self.training_run.id} has already been used to create observation:"
        f" {self.training_run.observation_id}."
        " No new checkpoints can be created."
      )

    new_checkpoint = self.create_checkpoint(params, self.experiment, self.training_run, checkpoints)
    now = new_checkpoint.created
    self.services.checkpoint_service.insert_checkpoints([new_checkpoint])
    self.services.training_run_service.mark_as_updated(self.training_run, now)
    if self.experiment:
      self.services.experiment_service.mark_as_updated(self.experiment, now)
    return CheckpointJsonBuilder(new_checkpoint)

  def _get_max_checkpoints(self, experiment):
    max_checkpoints = 200
    return max_checkpoints

  def create_checkpoint(self, params, experiment, training_run, checkpoints):
    checkpoint = Checkpoint(training_run_id=training_run.id)
    checkpoint.data = self.create_checkpoint_data(params, experiment, training_run, checkpoints)
    return checkpoint

  def create_checkpoint_data(self, params, experiment, training_run, checkpoints):
    return CheckpointData(
      values=params.values,
      metadata=params.metadata,
    )
