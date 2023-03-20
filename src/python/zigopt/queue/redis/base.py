# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
import uuid

from zigopt.queue.provider import QueueProvider


DIVIDER = ":"


class BaseRedisQueueProvider(QueueProvider):
  """
    A QueueProvider that uses Redis as the backend for queue messages.
    Uses Redis to reprioritize messages, if applicable
    """

  test_key_prefix = "test"

  def __init__(self, services, queue_name, wait_time_seconds=None):
    super().__init__(services, queue_name)
    self.redis_key = self.get_queue_name_key(services, queue_name)
    self.wait_time_seconds = wait_time_seconds

  def test(self):
    redis_test_key = self._get_randomized_test_key(self.services)
    self.services.redis_service.set_expire(redis_test_key, datetime.timedelta(minutes=1))
    test_message_data = self._make_test_message_data(str(uuid.uuid1()).encode())
    self._add_to_queue(redis_test_key, test_message_data)
    result_data = self._pop_from_queue(redis_test_key, 1)
    self.services.redis_service.delete(redis_test_key)
    self._check_test_message_data(test_message_data, result_data)

  @classmethod
  def _get_randomized_test_key(cls, services):
    return services.redis_key_service.create_queue_name_key(cls.test_key_prefix, str(uuid.uuid1()), DIVIDER)

  @classmethod
  def get_queue_name_key(cls, services, queue_name):
    return services.redis_key_service.create_queue_name_key(cls.redis_key_prefix, queue_name, DIVIDER)

  def delete(self, session, received_message):
    pass

  def reject(self, session, received_message):
    # TODO(SN-1120): can we support reject by re-enqueueing?
    # would need to make sure we don't get stuck in a loop forever
    pass

  def purge_queue(self):
    self.services.redis_service.delete(self.redis_key)

  def _add_to_queue(self, redis_key, messages):
    raise NotImplementedError()

  def _pop_from_queue(self, redis_key, wait_time_seconds):
    raise NotImplementedError()

  @classmethod
  def _make_test_message_data(cls, random_content):
    raise NotImplementedError()

  @classmethod
  def _check_test_message_data(cls, test_message_data, result_data):
    raise NotImplementedError()
