# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.gen.queue.messages_pb2 import MessageWithName
from zigopt.queue.message import ReceivedMessage
from zigopt.queue.redis.base import BaseRedisQueueProvider
from zigopt.redis.service import RedisServiceTimeoutError


class RedisMessageQueueProvider(BaseRedisQueueProvider):
  """
    Redis-based message queue.

    Uses Redis lists to process each message as they arrive.
    """

  redis_key_prefix = "messages"

  @property
  def requires_group_key(self):
    return False

  def enqueue(self, queue_messages, group_key, enqueue_time, message_score):
    redis_messages = [
      MessageWithName(
        message_type=q.message_type,
        serialized_body=q.serialized_body,
        enqueue_time=enqueue_time,
      ).SerializeToString()
      for q in queue_messages
    ]
    self._add_to_queue(self.redis_key, redis_messages)

  def dequeue(self, wait_time_seconds=None):
    wait_time_seconds = coalesce(wait_time_seconds, self.wait_time_seconds)
    redis_body = self._pop_from_queue(self.redis_key, wait_time_seconds)
    if redis_body is None:
      return redis_body
    message_with_name = self._parse_redis_body(redis_body)
    queue_message = self.services.message_router.deserialize_message(
      message_with_name.message_type,
      message_with_name.serialized_body,
    )
    return ReceivedMessage(
      queue_message,
      handle=None,
      enqueue_time=message_with_name.enqueue_time,
      group_key=None,
    )

  def count_queued_messages(self):
    return self.services.redis_service.count_list(self.redis_key)

  def _add_to_queue(self, redis_key, messages):
    self.services.redis_service.list_push(redis_key, *messages)

  def _pop_from_queue(self, redis_key, wait_time_seconds):
    try:
      response = self.services.redis_service.blocking_list_pop([redis_key], timeout=wait_time_seconds)
    except RedisServiceTimeoutError:
      return None
    if not response:
      return None
    _, redis_body = response
    return redis_body

  def _parse_redis_body(self, redis_body):
    message_with_name = MessageWithName()
    message_with_name.ParseFromString(redis_body)
    return message_with_name

  @classmethod
  def _make_test_message_data(cls, random_content):
    return [random_content]

  @classmethod
  def _check_test_message_data(cls, test_message_data, result_data):
    assert test_message_data == [result_data]
