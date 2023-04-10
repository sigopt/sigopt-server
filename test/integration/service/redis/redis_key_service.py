# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import pytest

from zigopt.queue.message_types import MessageType

from integration.service.test_base import ServiceBase


class TestRedisKeyService(ServiceBase):
  ARGS = {
    "divider": ":",
    "experiment_id": "1",
    "group_key": "1:1",
    "message_type": MessageType.OPTIMIZE,
    "authorization_url": "https://some.external.com/api?param=key",
    "queue_name": "redis-key-service-test-queue",
    "redis_key_prefix": "test",
    "source_name": "test_source",
    "source_number": 2,
  }

  @pytest.fixture(scope="class")
  def args(self):
    return deepcopy(self.ARGS)

  @pytest.fixture(scope="class")
  def bytes_args(self):
    return {k: bytes(str(v), "ascii") if v is not None else v for k, v in self.ARGS.items()}

  def get_key_values(self, key_map):
    return [key_obj.key_value for key_obj in key_map.values()]

  def get_key_map(self, services, args_map):
    key_map = {}

    key_map["sources_key"] = services.redis_key_service.create_sources_key(args_map["experiment_id"])
    key_map["suggestion_protobuf_key"] = services.redis_key_service.create_suggestion_protobuf_key(
      args_map["experiment_id"],
      args_map["source_number"],
    )
    key_map["suggestion_timestamp_key"] = services.redis_key_service.create_suggestion_timestamp_key(
      args_map["experiment_id"],
      args_map["source_number"],
    )
    key_map["queue_message_key"] = services.redis_key_service.create_queue_message_key(
      args_map["message_type"],
      args_map["group_key"],
      args_map["divider"],
    )
    key_map["queue_name_key"] = services.redis_key_service.create_queue_name_key(
      args_map["redis_key_prefix"],
      args_map["queue_name"],
      args_map["divider"],
    )
    return key_map

  def test_keys_are_unique(self, services, args, bytes_args):
    for args_map in [args, bytes_args]:
      key_map = self.get_key_map(services, args_map)
      key_values = self.get_key_values(key_map)
      assert len(set(key_values)) == len(key_values)

  def test_args_and_bytes_args_give_same_keys(self, services, args, bytes_args):
    key_map = self.get_key_map(services, args)
    key_values = self.get_key_values(key_map)
    bytes_key_map = self.get_key_map(services, bytes_args)
    bytes_key_values = self.get_key_values(bytes_key_map)

    assert key_values == bytes_key_values
