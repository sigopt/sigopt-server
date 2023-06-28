# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime

import pytest

from zigopt.common.conversions import maybe_decode
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.exception.logger import SoftException

from integration.service.test_base import ServiceBase


class TestRedisService(ServiceBase):
  # pylint: disable=too-many-public-methods
  @pytest.fixture
  def hash_mapping(self):
    return {
      "member1": "value1",
      "member2": "value2",
    }

  @pytest.fixture
  def hash_bytes_mapping(self, hash_mapping):
    return {bytes(k, "ascii"): bytes(v, "ascii") for k, v in hash_mapping.items()}

  @pytest.fixture
  def sorted_set_key(self, services):
    return self.make_redis_key(services, "sorted_set_key")

  @pytest.fixture
  def sorted_set_keys_for_bzpop(self, services):
    return [self.make_redis_key(services, b"sorted_set_key_for_bz_pop")]

  @pytest.fixture
  def set_key(self, services):
    return self.make_redis_key(services, "set_key")

  @pytest.fixture
  def hash_key(self, services):
    return self.make_redis_key(services, "hash_key")

  def make_redis_key(self, services, key_value):
    # pylint: disable=protected-access
    return services.redis_key_service._RedisKey(maybe_decode(key_value))
    # pylint: enable=protected-access

  def test_add_sorted_set_new(self, services):
    sorted_set_key = self.make_redis_key(services, "ss_key")
    assert services.redis_service.count_sorted_set(sorted_set_key) == 0

    member, score = "member1", 1.0
    num_added = services.redis_service.add_sorted_set_new(sorted_set_key, [(member, score)])
    assert num_added == 1
    assert services.redis_service.count_sorted_set(sorted_set_key) == 1

    # trying to add same member doesn't duplicate members nor override score
    num_added = services.redis_service.add_sorted_set_new(sorted_set_key, [(member, score + 1)])
    assert num_added == 0
    assert services.redis_service.count_sorted_set(sorted_set_key) == 1
    _, stored_score = services.redis_service.get_sorted_set_range(sorted_set_key, 0, -1, withscores=True)[0]
    assert stored_score == score

  def test_get_sorted_set_range(self, services, sorted_set_key):
    member1, score1 = "member1", 1.0
    member2, score2 = "member2", 2.0
    member3, score3 = "member3", 3.0
    services.redis_service.add_sorted_set_new(
      sorted_set_key,
      [
        (member1, score1),
        (member2, score2),
        (member3, score3),
      ],
    )

    # get smallest element:
    members = services.redis_service.get_sorted_set_range(sorted_set_key, 0, 0)
    assert members == [bytes(member1, "ascii")]

    # get 2 smallest elements:
    members = services.redis_service.get_sorted_set_range(sorted_set_key, 0, 1)
    assert members == [bytes(member1, "ascii"), bytes(member2, "ascii")]

    # get largest element
    members = services.redis_service.get_sorted_set_range(sorted_set_key, 0, 0, reverse=True)
    assert members == [bytes(member3, "ascii")]

  def test_remove_from_sorted_set(self, services, sorted_set_key):
    member1, score1 = "member1", 1.0
    member2, score2 = "member2", 2.0
    services.redis_service.add_sorted_set_new(sorted_set_key, [(member1, score1)])

    num_removed = services.redis_service.remove_from_sorted_set(sorted_set_key, member1)
    assert num_removed == 1
    assert services.redis_service.count_sorted_set(sorted_set_key) == 0

    # remove multiple members at once
    services.redis_service.add_sorted_set_new(sorted_set_key, [(member1, score1), (member2, score2)])

    num_removed = services.redis_service.remove_from_sorted_set(sorted_set_key, member1, member2)
    assert num_removed == 2
    assert services.redis_service.count_sorted_set(sorted_set_key) == 0

    # removing non-existent element doesn't add to count
    num_removed = services.redis_service.remove_from_sorted_set(sorted_set_key, member1)
    assert num_removed == 0

    # removing no members (empty list expansion) returns 0
    num_removed = services.redis_service.remove_from_sorted_set(sorted_set_key)
    assert num_removed == 0

  def test_add_to_set(self, services, set_key):
    member1 = "member1"
    assert services.redis_service.get_set_members(set_key) == []
    services.redis_service.add_to_set(set_key, member1)
    assert services.redis_service.get_set_members(set_key) == [bytes(member1, "ascii")]

  def test_get_set_members(self, services, set_key):
    member1, member2 = "member1", "member2"
    assert services.redis_service.get_set_members(set_key) == []
    services.redis_service.add_to_set(set_key, member1)
    assert services.redis_service.get_set_members(set_key) == [bytes(member1, "ascii")]

    services.redis_service.add_to_set(set_key, member2)
    expected_members = [bytes(member1, "ascii"), bytes(member2, "ascii")]
    observed_members = services.redis_service.get_set_members(set_key)
    assert sorted(expected_members) == sorted(observed_members)

  def test_set_hash_fields(self, services, hash_mapping, hash_bytes_mapping, hash_key):
    services.redis_service.set_hash_fields(hash_key, hash_mapping)

    observed_mapping = services.redis_service.get_all_hash_fields(hash_key)
    assert observed_mapping == hash_bytes_mapping

  def test_get_all_hash_fields(self, services, hash_mapping, hash_bytes_mapping, hash_key):
    services.redis_service.set_hash_fields(hash_key, hash_mapping)

    observed_mapping = services.redis_service.get_all_hash_fields(hash_key)
    assert observed_mapping == hash_bytes_mapping

  def test_remove_from_hash(self, services, hash_mapping, hash_bytes_mapping, hash_key):
    services.redis_service.set_hash_fields(hash_key, hash_mapping)
    key1, key2, *_ = hash_mapping.keys()

    services.redis_service.remove_from_hash(hash_key, key1)

    remaining_mapping = services.redis_service.get_all_hash_fields(hash_key)
    assert bytes(key1, "ascii") not in remaining_mapping
    assert bytes(key2, "ascii") in remaining_mapping

  def test_dangerously_purge_database(self, services, sorted_set_key, set_key):
    services.redis_service.add_sorted_set_new(sorted_set_key, [("member1", 1.0)])
    services.redis_service.add_to_set(set_key, "set_member1")

    services.redis_service.dangerously_purge_database()
    assert services.redis_service.count_sorted_set(sorted_set_key) == 0
    assert services.redis_service.get_set_members(set_key) == []

  def test_blocking_pop_min_from_sorted_set(self, services, sorted_set_keys_for_bzpop):
    services.redis_service.add_sorted_set_new(
      sorted_set_keys_for_bzpop[0],
      [
        (b"member1", 1.0),
        (b"member2", 2.0),
      ],
    )
    bytes_key_value = bytes(services.redis_key_service.get_key_value(sorted_set_keys_for_bzpop[0]), "ascii")

    (popped_key_value, value, score) = services.redis_service.blocking_pop_min_from_sorted_set(
      sorted_set_keys_for_bzpop,
      timeout=2,
    )
    assert (popped_key_value, value, score) == (bytes_key_value, b"member1", 1.0)

    (popped_key_value, value, score) = services.redis_service.blocking_pop_min_from_sorted_set(
      sorted_set_keys_for_bzpop, timeout=2
    )
    assert (popped_key_value, value, score) == (bytes_key_value, b"member2", 2.0)

    ret = services.redis_service.blocking_pop_min_from_sorted_set(sorted_set_keys_for_bzpop, timeout=2)
    assert ret is None

    with pytest.raises(SoftException):
      services.redis_service.blocking_pop_min_from_sorted_set(
        sorted_set_keys_for_bzpop, services.redis_service.POLLING_TIMEOUT + 1
      )

  def test_blocking_list_pop(self, services):
    list_key_value = "list_key"
    bytes_key_value = bytes(list_key_value, "ascii")
    list_keys = [self.make_redis_key(services, list_key_value)]

    services.redis_service.list_push(list_keys[0], *[b"member1", b"member2"])

    (popped_key_value, value) = services.redis_service.blocking_list_pop(list_keys, timeout=2)
    assert (popped_key_value, value) == (bytes_key_value, b"member1")

    (popped_key_value, value) = services.redis_service.blocking_list_pop(list_keys, timeout=2)
    assert (popped_key_value, value) == (bytes_key_value, b"member2")

    ret = services.redis_service.blocking_list_pop(list_keys, timeout=2)
    assert ret is None

    with pytest.raises(SoftException):
      services.redis_service.blocking_list_pop(list_keys, services.redis_service.POLLING_TIMEOUT + 1)

  def test_increment(self, services):
    incr_key = self.make_redis_key(services, "incr_key")
    assert services.redis_service.get(incr_key) is None
    services.redis_service.increment(incr_key)
    assert services.redis_service.get(incr_key) == b"1"
    services.redis_service.increment(incr_key)
    assert services.redis_service.get(incr_key) == b"2"

  def test_exists(self, services):
    exist_key = self.make_redis_key(services, "exist_key")
    assert services.redis_service.exists(exist_key) is False
    services.redis_service.increment(exist_key)
    assert services.redis_service.exists(exist_key) is True
    services.redis_service.delete(exist_key)
    assert services.redis_service.exists(exist_key) is False

  def _seconds_from_now(self, seconds):
    return current_datetime() + datetime.timedelta(seconds=seconds)

  def test_set_expire_at(self, services):
    expire_at_key = self.make_redis_key(services, "expire_at_key")
    assert services.redis_service.exists(expire_at_key) is False

    services.redis_service.set_expire_at(expire_at_key, self._seconds_from_now(1))
    assert services.redis_service.exists(expire_at_key) is False

    services.redis_service.increment(expire_at_key)
    services.redis_service.set_expire_at(expire_at_key, self._seconds_from_now(1))
    assert services.redis_service.exists(expire_at_key) is True
    services.redis_service.set_expire_at(expire_at_key, self._seconds_from_now(-1))
    assert services.redis_service.exists(expire_at_key) is False

  def test_set_expire(self, services):
    expire_key = self.make_redis_key(services, "expire_key")
    assert services.redis_service.exists(expire_key) is False

    one_second_timedelta = datetime.timedelta(seconds=1)

    services.redis_service.set_expire(expire_key, one_second_timedelta)
    assert services.redis_service.exists(expire_key) is False

    services.redis_service.increment(expire_key)
    services.redis_service.set_expire(expire_key, one_second_timedelta)
    assert services.redis_service.exists(expire_key) is True
    services.redis_service.set_expire(expire_key, -one_second_timedelta)
    assert services.redis_service.exists(expire_key) is False
