# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import deque

from zigopt.common import *
from zigopt.queue.base import BaseQueueService
from zigopt.queue.message import BaseMessageBody, ReceivedMessage
from zigopt.queue.workers import QueueMessageHandler


class LocalQueueService(BaseQueueService):
  # HACK: RequestLocalServiceBag gets passed in and is used to construct
  # a fresh service bag for each asynchronously consumed queue message.
  # This is to manage the circular dependency, so that LocalQueueService does not depend
  # on RequestLocalServiceBag
  def __init__(self, services, request_local_cls):
    super().__init__(services)
    self._request_local_cls = request_local_cls
    self._buffer = deque[tuple[BaseMessageBody, float]]([])
    self._corked = False

  def warmup(self):
    pass

  def count_queued_messages(self, queue_name):
    return 0

  def _enqueue_batch(self, queue_messages, group_key, enqueue_time, message_score):
    for queue_message in queue_messages:
      self._buffer.append((queue_message, enqueue_time))
    self._consume_all_buffered()

  def _consume_all_buffered(self):
    if not self._corked:
      try:
        while self._buffer:
          self.consume_message(*self._buffer.popleft())
      finally:
        self._buffer.clear()

  def consume_message(self, queue_message, enqueue_time):
    workers = QueueMessageHandler(global_services=self.services)
    WorkerClass = self.services.message_router.get_worker_class_for_message(queue_message.message_type)
    services = self._request_local_cls(self.services)
    services.database_service.start_session()
    if WorkerClass:
      queue_name = self.get_queue_name_from_message_type(queue_message.message_type)
      received_message = ReceivedMessage(
        queue_message=queue_message,
        handle=None,
        enqueue_time=enqueue_time,
      )
      workers.monitor_message(
        services,
        queue_name,
        received_message,
      )
      workers.submit(WorkerClass, services, received_message)
    services.database_service.end_session()
