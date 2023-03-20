# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64

from zigopt.common import *
from zigopt.queue.message import ReceivedMessage
from zigopt.queue.message_types import MessageType
from zigopt.queue.redis.base import BaseRedisQueueProvider
from zigopt.redis.service import RedisServiceTimeoutError


DIVIDER = ":"


class RedisOptimizeQueueProvider(BaseRedisQueueProvider):
  """
    Redis-based optimization queue

    Uses Redis sorted sets to order messages by timestamp.
    Messages are stored uniquely in the queue by key.
    Key insertions do not overwrite existing values, so messages remain in queue with fixed timestamps until processed
    """

  redis_key_prefix = "queue"

  @property
  def requires_group_key(self):
    return True

  def enqueue(self, queue_messages, group_key, enqueue_time, message_score):
    queue_messages_by_key = to_map_by_key(
      queue_messages,
      lambda queue_message: self._unparse_message_key(queue_message.message_type, group_key),
    )
    message_keys_to_scores = {
      message_key: coalesce(message_score, enqueue_time) for message_key in queue_messages_by_key
    }

    self._persist_message_contents(queue_messages, group_key)
    self._add_to_queue(self.redis_key, message_keys_to_scores)

  def dequeue(self, session, wait_time_seconds=None):
    wait_time_seconds = coalesce(wait_time_seconds, self.wait_time_seconds)
    message_key, enqueue_time = self._pop_from_queue(self.redis_key, wait_time_seconds)
    if not message_key:
      return None
    queue_message = self._retrieve_message_contents(message_key)
    if not queue_message:
      return None
    _, group_key = self._parse_message_key(message_key)
    return ReceivedMessage(
      queue_message,
      handle=None,
      enqueue_time=enqueue_time,
      group_key=group_key,
    )

  def count_queued_messages(self):
    return self.services.redis_service.count_sorted_set(self.redis_key)

  def _add_to_queue(self, redis_key, messages):
    self.services.redis_service.add_sorted_set_new(redis_key, messages)

  def _pop_from_queue(self, redis_key, wait_time_seconds):
    try:
      response = self.services.redis_service.blocking_pop_min_from_sorted_set(
        [redis_key],
        timeout=wait_time_seconds,
      )
    except RedisServiceTimeoutError:
      return None, None
    if not response:
      return None, None
    (_, message_key, enqueue_time) = response
    return message_key, enqueue_time

  def _is_persisted_message_type(self, message_type):
    if message_type in (MessageType.NEXT_POINTS, MessageType.OPTIMIZE):
      return True
    return False

  def _parse_message_key(self, message_key):
    message_type, group_key = message_key.decode("utf-8").split(DIVIDER, 1)
    return message_type, group_key

  def _unparse_message_key(self, message_type, group_key):
    redis_key = self._get_redis_key(message_type, group_key)
    return self.services.redis_key_service.get_key_value(redis_key)

  def _encode_serialized_body(self, serialized_body):
    return base64.b64encode(serialized_body)

  def _decode_serialized_body(self, serialized_body):
    return base64.b64decode(serialized_body)

  def _get_redis_key(self, message_type, group_key):
    return self.services.redis_key_service.create_queue_message_key(message_type, group_key, DIVIDER)

  def _persist_message_contents(self, queue_messages, group_key):
    for queue_message in queue_messages:
      if self._is_persisted_message_type(queue_message.message_type):
        redis_key = self._get_redis_key(queue_message.message_type, group_key)
        serialized_body = self._encode_serialized_body(queue_message.serialized_body)
        # TODO(SN-1121): Could use mset here, but need `set` if we want to set an expiry_time
        self.services.redis_service.set(
          redis_key,
          serialized_body,
          self.services.config_broker.get("queue.redis_key_expiry_time", 4 * 60 * 60),
        )
      else:
        self._validate_unpersisted_deserialized_message(queue_message.deserialized_message, group_key)

  def _retrieve_message_contents(self, message_key):
    message_type, group_key = self._parse_message_key(message_key)
    if self._is_persisted_message_type(message_type):
      redis_key = self._get_redis_key(message_type, group_key)
      persisted_redis_message = self.services.redis_service.get(redis_key)
      if not persisted_redis_message:
        self.services.exception_logger.soft_exception(f"No persisted message was found for {message_key}")
        return None
      serialized_body = self._decode_serialized_body(persisted_redis_message)
      message = self.services.message_router.deserialize_message(message_type, serialized_body)
    else:
      message = self.services.message_router.make_queue_message(message_type)
      self._populate_unpersisted_deserialized_message(message.deserialized_message, group_key)
    return message

  def _validate_unpersisted_deserialized_message(self, deserialized_message, group_key):
    assert hasattr(deserialized_message, "force")
    self.services.queue_message_grouper.validate_unpersisted_deserialized_message(deserialized_message, group_key)

  def _populate_unpersisted_deserialized_message(self, deserialized_message, group_key):
    deserialized_message.force = True
    self.services.queue_message_grouper.apply_to_deserialized_message(deserialized_message, group_key)

  @classmethod
  def _make_test_message_data(cls, random_content):
    return {random_content: 1}

  @classmethod
  def _check_test_message_data(cls, test_message_data, result_data):
    (test_content,) = test_message_data.items()
    assert list(test_content) == list(result_data)
