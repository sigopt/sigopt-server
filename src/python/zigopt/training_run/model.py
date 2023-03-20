# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import (
  BigInteger,
  Boolean,
  Column,
  ForeignKey,
  ForeignKeyConstraint,
  Index,
  PrimaryKeyConstraint,
  UniqueConstraint,
)
from sqlalchemy.orm import validates

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.util import get_observation_values_dict_from_training_run


OPTIMIZED_ASSIGNMENT_SOURCE = "SigOpt"


def is_completed_state(training_run_state):
  return training_run_state in (TrainingRunData.COMPLETED, TrainingRunData.FAILED)


class TrainingRun(Base):
  __tablename__ = "training_runs"

  id = Column(BigInteger, name="id", primary_key=True)
  project_id = Column(BigInteger, name="project_id")

  client_id = Column(
    BigInteger,
    ForeignKey("clients.id", ondelete="RESTRICT", name="training_runs_client_id_fkey"),
    name="client_id",
    nullable=False,
  )
  created_by = Column(
    BigInteger,
    ForeignKey("users.id", ondelete="SET NULL", name="training_runs_created_by_fkey"),
    name="created_by",
  )
  experiment_id = Column(
    BigInteger,
    ForeignKey("experiments.id", name="training_runs_experiment_id_fkey"),
    name="experiment_id",
  )
  suggestion_id = Column(
    BigInteger,
    ForeignKey("suggestions_processed.suggestion_id", name="training_runs_suggestion_id_fkey"),
    name="suggestion_id",
  )
  observation_id = Column(
    BigInteger,
    ForeignKey("observations.id", name="training_runs_observation_id_fkey"),
    name="observation_id",
  )

  created = Column(ImpliedUTCDateTime, name="created", nullable=False)
  updated = Column(ImpliedUTCDateTime, name="updated", nullable=False)
  deleted = Column(Boolean, name="deleted", default=False, nullable=False)
  completed = Column(ImpliedUTCDateTime, name="completed")

  training_run_data = ProtobufColumn(TrainingRunData, nullable=False, name="data")

  __table_args__ = tuple(
    [
      PrimaryKeyConstraint("id", name="training_runs_pkey"),
      UniqueConstraint("observation_id", name="training_runs_observation_id_key"),
      UniqueConstraint("suggestion_id", name="training_runs_suggestion_id_key"),
      ForeignKeyConstraint(
        ["project_id", "client_id"],
        ["projects.id", "projects.client_id"],
        ondelete="RESTRICT",
        name="training_runs_project_id_fkey",
      ),
      Index("ix_training_runs_experiment_id_id", "experiment_id", "id"),
      Index("ix_training_runs_client_id_project_id_id", "client_id", "project_id", "id"),
    ]
  )

  def __init__(self, *args, **kwargs):
    kwargs.setdefault(TrainingRun.created.key, current_datetime())
    kwargs.setdefault(TrainingRun.updated.key, kwargs[TrainingRun.created.key])
    kwargs.setdefault(TrainingRun.deleted.key, False)
    kwargs.setdefault(TrainingRun.training_run_data.key, TrainingRun.training_run_data.default_value())
    if is_completed_state(kwargs["training_run_data"].state):
      kwargs.setdefault(TrainingRun.completed.key, kwargs[TrainingRun.updated.key])
    super().__init__(*args, **kwargs)

  @validates("training_run_data")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  @property
  def state(self):
    if self.training_run_data.state:
      return self.training_run_data.state
    if self.completed:
      return TrainingRunData.COMPLETED
    return TrainingRunData.ACTIVE

  def get_observation_values(self, experiment):
    return get_observation_values_dict_from_training_run(experiment, self)
