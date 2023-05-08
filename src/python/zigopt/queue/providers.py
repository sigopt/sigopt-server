# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import collections

from zigopt.common import *
from zigopt.queue.provider import QueueProviderType
from zigopt.queue.redis.message import RedisMessageQueueProvider
from zigopt.queue.redis.optimize import RedisOptimizeQueueProvider


@generator_to_list
def make_providers(services):
  assert services.config_broker.get("queue.type", default="async") == "async"
  queues = services.config_broker["queues"]
  queue_names = [q["name"] for q in queues]
  queue_name_counts = collections.Counter(queue_names)
  duplicate_names = [key for key, value in queue_name_counts.items() if value > 1]
  if duplicate_names:
    raise Exception(f"queues.*.name must be unique, got duplicates for: {duplicate_names}")
  for queue_info in queues:
    provider = queue_info["provider"]
    queue_name = queue_info["name"]
    if provider == QueueProviderType.REDIS_OPTIMIZE:
      yield RedisOptimizeQueueProvider(
        services,
        queue_name=queue_name,
        wait_time_seconds=queue_info.get("wait_time_seconds", 20),
      )
    else:
      assert provider == QueueProviderType.REDIS_MESSAGE
      yield RedisMessageQueueProvider(
        services,
        queue_name=queue_name,
        wait_time_seconds=queue_info.get("wait_time_seconds", 20),
      )
