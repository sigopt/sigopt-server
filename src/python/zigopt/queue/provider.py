# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.queue.message import QueueMessage


class QueueProviderType:
  REDIS_OPTIMIZE = "redis-optimize"
  REDIS_MESSAGE = "redis-message"


class QueueProvider:
  queue_name: str

  # Implemented by subclasses
  def __init__(self, services, queue_name: str):
    self.services = services
    self.queue_name = queue_name

  @property
  def requires_group_key(self) -> bool:
    return False

  def warmup(self) -> None:
    pass

  def count_queued_messages(self) -> int:
    raise NotImplementedError()

  def test(self) -> None:
    raise NotImplementedError()

  def enqueue(
    self,
    queue_messages: Sequence[QueueMessage],
    group_key: str,
    enqueue_time: int,
    message_score: float,
  ) -> None:
    raise NotImplementedError()

  def dequeue(self, wait_time_seconds: float | None = None) -> QueueMessage:
    raise NotImplementedError()

  def delete(self, received_message: QueueMessage) -> None:
    raise NotImplementedError()

  def reject(self, received_message: QueueMessage) -> None:
    raise NotImplementedError()

  def purge_queue(self) -> None:
    raise NotImplementedError()
