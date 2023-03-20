# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.queue.base import BaseQueueService


class DequeueSession(object):
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, tb):
    pass


class QueueService(BaseQueueService):
  def __init__(self, services, providers):
    super().__init__(services)
    self.enabled = self.services.config_broker.get("queue.enabled", default=True)
    self.providers = providers

  def warmup(self):
    if self.enabled:
      for provider in self.providers:
        provider.warmup()

  def purge_all_queues(self):
    if self.enabled:
      for provider in self.providers:
        provider.purge_queue()

  def count_queued_messages(self, queue_name):
    return self.get_provider_from_queue_name(queue_name).count_queued_messages()

  def _enqueue_batch(self, queue_messages, group_key, enqueue_time, message_score):
    if self.enabled:
      for (provider, queue_message_batch) in as_grouped_dict(
        queue_messages,
        lambda m: self.get_provider_from_message_type(m.message_type),
      ).items():
        assert group_key or not provider.requires_group_key, "Group key not provided"
        provider.enqueue(
          queue_message_batch,
          group_key=group_key,
          enqueue_time=enqueue_time,
          message_score=message_score,
        )

  def start_session(self, queue_name):
    provider = self.get_provider_from_queue_name(queue_name)
    if provider is None:
      raise ValueError(f"{queue_name} has no provider")
    if hasattr(provider, "start_session"):
      return provider.start_session()
    return DequeueSession()

  def test(self, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).test()

  def dequeue(self, session, queue_name, wait_time_seconds=None):
    if self.enabled:
      return self.get_provider_from_queue_name(queue_name).dequeue(session, wait_time_seconds=wait_time_seconds)
    return None

  def delete(self, session, message, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).delete(session, message)

  def reject(self, session, message, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).reject(session, message)

  def get_provider_from_queue_name(self, queue_name):
    return find(self.providers, lambda p: p.queue_name == queue_name)

  def get_provider_from_message_type(self, message_type):
    queue_name = self.get_queue_name_from_message_type(message_type)
    return self.get_provider_from_queue_name(queue_name)
