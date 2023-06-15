# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.queue.message import QueueMessage
from zigopt.services.base import Service


class BaseQueueService(Service):
  def warmup(self) -> None:
    raise NotImplementedError()

  def count_queued_messages(self, queue_name: str) -> int:
    raise NotImplementedError()

  def enqueue_batch(
    self,
    queue_messages: Sequence[QueueMessage],
    group_key: str | None = None,
    enqueue_time: int | None = None,
    message_score: float | None = None,
  ) -> None:
    self._enqueue_batch(
      queue_messages=queue_messages,
      group_key=group_key,
      enqueue_time=coalesce(enqueue_time, unix_timestamp()),
      message_score=message_score,
    )

  def _enqueue_batch(
    self,
    queue_messages: Sequence[QueueMessage],
    group_key: str | None,
    enqueue_time: int | None,
    message_score: float | None,
  ) -> None:
    raise NotImplementedError()

  def get_queue_name_from_message_type(self, message_type: str) -> str:
    return self.services.message_router.get_queue_name_from_message_type(message_type)

  def make_and_enqueue_message(self, _message_type: str, *args, **kwargs) -> None:
    self.enqueue_batch([self.services.message_router.make_queue_message(_message_type, *args, **kwargs)])
