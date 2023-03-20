# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.services.base import Service


class BaseQueueService(Service):
  def warmup(self):
    raise NotImplementedError()

  def count_queued_messages(self, queue_name):
    raise NotImplementedError()

  def enqueue_batch(self, queue_messages, group_key=None, enqueue_time=None, message_score=None):
    self._enqueue_batch(
      queue_messages=queue_messages,
      group_key=group_key,
      enqueue_time=coalesce(enqueue_time, unix_timestamp()),
      message_score=message_score,
    )

  def _enqueue_batch(self, queue_messages, group_key, enqueue_time, message_score):
    raise NotImplementedError()

  def get_queue_name_from_message_type(self, message_type):
    return self.services.message_router.get_queue_name_from_message_type(message_type)

  def make_and_enqueue_message(self, _message_type, *args, **kwargs):
    self.enqueue_batch([self.services.message_router.make_queue_message(_message_type, *args, **kwargs)])
