# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.queue.provider import QueueProviderType
from zigopt.queue.redis.message import RedisMessageQueueProvider
from zigopt.queue.redis.optimize import RedisOptimizeQueueProvider


@generator_to_list
def make_providers(services):
  assert services.config_broker.get("queue.type", default="async") == "async"
  queues = services.config_broker["queues"]
  assert len(queues) == len(distinct_by(queues, lambda q: q["name"]))
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
