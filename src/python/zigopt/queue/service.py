# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.queue.base import BaseQueueService
from zigopt.queue.provider import QueueProvider


class QueueService(BaseQueueService):
  providers: Sequence[QueueProvider]
  enabled: bool

  def __init__(self, services, providers: Sequence[QueueProvider]):
    super().__init__(services)
    self.enabled = self.services.config_broker.get("queue.enabled", default=True)
    self.providers = providers

  def warmup(self):
    if self.enabled:
      for provider in self.providers:
        provider.warmup()

  def purge_all_queues(self) -> None:
    if self.enabled:
      for provider in self.providers:
        provider.purge_queue()

  def count_queued_messages(self, queue_name):
    return self.get_provider_from_queue_name(queue_name).count_queued_messages()

  def _enqueue_batch(self, queue_messages, group_key, enqueue_time, message_score):
    if self.enabled:
      for provider, queue_message_batch in as_grouped_dict(
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

  def test(self, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).test()

  def dequeue(self, queue_name, wait_time_seconds=None):
    if self.enabled:
      return self.get_provider_from_queue_name(queue_name).dequeue(wait_time_seconds=wait_time_seconds)
    return None

  def delete(self, message, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).delete(message)

  def reject(self, message, queue_name):
    if self.enabled:
      self.get_provider_from_queue_name(queue_name).reject(message)

  def get_provider_from_queue_name(self, queue_name: str) -> QueueProvider:
    provider = find(self.providers, lambda p: p.queue_name == queue_name)
    assert provider
    return provider

  def get_provider_from_message_type(self, message_type: str) -> QueueProvider:
    queue_name = self.get_queue_name_from_message_type(message_type)
    return self.get_provider_from_queue_name(queue_name)
