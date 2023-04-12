# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKey, Index
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.data.model import BaseHasMeasurementsProxy
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.checkpoint.checkpoint_data_pb2 import CheckpointData


CHECKPOINT_MAX_METADATA_FIELDS = 5


class CheckpointDataProxy(BaseHasMeasurementsProxy):
  def sorted_measurements(self):
    return sorted(self.values, key=lambda val: val.name)

  # NOTE: currently checkpoints cannot fail, but this helps enables cleaner methods in BaseHasMeasurementsProxy
  @property
  def reported_failure(self):
    return False


class Checkpoint(Base):
  __tablename__ = "checkpoints"

  id = Column(BigInteger, primary_key=True)
  training_run_id = Column(BigInteger, ForeignKey("training_runs.id"), nullable=False)
  created = Column(ImpliedUTCDateTime, nullable=False)
  data = ProtobufColumn(CheckpointData, proxy=CheckpointDataProxy, nullable=False)

  __table_args__ = tuple(
    [
      Index("ix_checkpoints_training_run_id_id", "training_run_id", "id"),
    ]
  )

  def __init__(self, *args, **kwargs):
    kwargs.setdefault(Checkpoint.data.key, Checkpoint.data.default_value())
    kwargs.setdefault(Checkpoint.created.key, current_datetime())
    super().__init__(*args, **kwargs)

  @validates("data")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=CheckpointDataProxy)

  def sorted_measurements(self):
    return self.data.sorted_measurements()

  def get_all_measurements(self, experiment):
    return self.data.get_all_measurements(experiment)

  def get_all_measurements_for_maximization(self, experiment):
    return self.data.get_all_measurements_for_maximization(experiment)

  def get_optimized_measurements_for_maximization(self, experiment):
    return self.data.get_optimized_measurements_for_maximization(experiment)

  def value_for_maximization(self, experiment, name):
    return self.data.value_for_maximization(experiment, name)

  def metric_value(self, experiment, name):
    return self.data.metric_value(experiment, name)

  def metric_value_var(self, experiment, name):
    return self.data.metric_value_var(experiment, name)
