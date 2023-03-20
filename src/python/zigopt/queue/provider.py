# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class QueueProviderType(object):
  REDIS_OPTIMIZE = "redis-optimize"
  REDIS_MESSAGE = "redis-message"


class QueueProvider(object):
  # Implemented by subclasses
  def __init__(self, services, queue_name):
    self.services = services
    self.queue_name = queue_name

  @property
  def requires_group_key(self):
    return False

  def warmup(self):
    pass

  def count_queued_messages(self):
    raise NotImplementedError()

  def test(self):
    raise NotImplementedError()

  def enqueue(self, queue_messages, group_key, enqueue_time, message_score):
    raise NotImplementedError()

  def dequeue(self, session, wait_time_seconds=None):
    raise NotImplementedError()

  def delete(self, session, received_message):
    raise NotImplementedError()

  def reject(self, session, received_message):
    raise NotImplementedError()

  def purge_queue(self):
    raise NotImplementedError()
