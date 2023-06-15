# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import contextlib
import uuid
from collections.abc import Generator

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.services.base import Service


class BaseMessageTrackingService(Service):
  def count_processing_messages(self, queue_name: str) -> int:
    raise NotImplementedError()

  @contextlib.contextmanager
  def process_one_message(self, queue_name: str) -> Generator:
    raise NotImplementedError()


class MessageTrackingService(BaseMessageTrackingService):
  def _get_redis_key(self, queue_name: str) -> str:
    return self.services.redis_key_service.create_queue_tracking_key(queue_name)

  def count_processing_messages(self, queue_name: str) -> int:
    key = self._get_redis_key(queue_name)
    return self.services.redis_service.count_sorted_set(key)

  @contextlib.contextmanager
  def process_one_message(self, queue_name: str) -> Generator:
    key = self._get_redis_key(queue_name)
    set_member = str(uuid.uuid1())
    now = unix_timestamp()
    self.services.redis_service.add_sorted_set_new(key, [(set_member, now)])
    try:
      yield
    finally:
      self.services.redis_service.remove_from_sorted_set(key, set_member)
