# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from sqlalchemy import func

from zigopt.common import *
from zigopt.checkpoint.model import Checkpoint
from zigopt.services.base import Service


class CheckpointService(Service):
  def insert_checkpoints(self, checkpoints: Sequence[Checkpoint]) -> None:
    self.services.database_service.insert_all(checkpoints)

  def find_by_id(self, checkpoint_id: int) -> Checkpoint | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Checkpoint).filter(Checkpoint.id == checkpoint_id)
    )

  def find_by_ids(self, checkpoint_ids: Sequence[int]) -> Sequence[Checkpoint]:
    if len(checkpoint_ids) == 0:
      return []
    query = self.services.database_service.query(Checkpoint).filter(Checkpoint.id.in_(checkpoint_ids))
    return self.services.database_service.all(query)

  def find_by_training_run_id(self, training_run_id: int) -> Sequence[Checkpoint]:
    query = (
      self.services.database_service.query(Checkpoint)
      .filter(Checkpoint.training_run_id == training_run_id)
      .order_by(Checkpoint.id)
    )
    return self.services.database_service.all(query)

  def count_by_training_run(self, training_run_id: int) -> int:
    return self.services.database_service.count(
      self.services.database_service.query(Checkpoint).filter(Checkpoint.training_run_id == training_run_id)
    )

  def count_by_training_run_ids(self, training_run_ids: int) -> dict[int, int]:
    return dict(
      self.services.database_service.all(
        self.services.database_service.query(Checkpoint.training_run_id, func.count(1))
        .filter(Checkpoint.training_run_id.in_(training_run_ids))
        .group_by(Checkpoint.training_run_id)
      )
    )
