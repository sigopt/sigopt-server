# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
import functools

import backoff
import redis

from zigopt.common import *
from zigopt.common.conversions import maybe_decode
from zigopt.common.lists import distinct, list_get
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.common.strings import is_string
from zigopt.services.base import Service


DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_SOCKET_PATH = "/var/run/redis/redis.sock"


class RedisServiceError(Exception):
  pass


class RedisServiceTimeoutError(RedisServiceError):
  pass


class SigOptUnixDomainSocketConnection(redis.UnixDomainSocketConnection):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.socket_timeout = kwargs.get("socket_timeout")


# Retries the query if there is a Redis timeout error. Only appropriate for idempotent calls
def retry_on_failure(func):
  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    NUM_RETRIES = self.services.config_broker.get("redis.num_retries", 1)
    NUM_RETRIES = max(NUM_RETRIES, 0)

    def warmup_on_exception(e):
      self.logger.warning(f"redis failed running {func.__name__}")
      self.warmup()
      return False

    return backoff.on_exception(
      backoff.expo,
      Exception,
      max_tries=NUM_RETRIES + 1,
      giveup=warmup_on_exception,
    )(lambda: func(self, *args, **kwargs))()

  return wrapper


def ensure_redis(func):
  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    if not self.redis or not self.blocking_conn_redis:
      self.warmup()
      if not self.redis or not self.blocking_conn_redis:
        uri = self.get_redis_uri()
        raise RedisServiceError(f"Attempting to access Redis but failed to connect to {uri}")
    return func(self, *args, **kwargs)

  return wrapper


def decode_args(func):
  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    new_args = [maybe_decode(a) for a in args]
    new_kwargs = {k: maybe_decode(v) for k, v in kwargs.items()}
    return func(self, *new_args, **new_kwargs)

  return wrapper


class RedisKeyService(Service):
  # Keeps track of all methods used to generate redis keys to ensure that there are no collisions

  DIVIDER = ":"
  QUEUE_TRACKING_PREFIX = "tracking"

  class _RedisKey(object):
    def __init__(self, key_value):
      assert is_string(key_value)
      self.key_value = key_value

  def get_key_value(self, redis_key):
    assert isinstance(redis_key, self._RedisKey)
    return redis_key.key_value

  @decode_args
  def create_sources_key(self, experiment_id):
    # redis responses are bytes-objects, cast to int to avoid b'...' in the str
    return self._RedisKey(f"experiment{self.DIVIDER}{int(experiment_id)}{self.DIVIDER}sources")

  @decode_args
  def create_suggestion_timestamp_key(self, experiment_id, source):
    return self._RedisKey(
      f"experiment{self.DIVIDER}"
      f"{int(experiment_id)}{self.DIVIDER}"
      f"source{self.DIVIDER}"
      f"{int(source)}{self.DIVIDER}"
      "suggestion_timestamps"
    )

  @decode_args
  def create_suggestion_protobuf_key(self, experiment_id, source_number):
    return self._RedisKey(
      f"experiment{self.DIVIDER}"
      f"{int(experiment_id)}{self.DIVIDER}"
      f"source{self.DIVIDER}"
      f"{int(source_number)}{self.DIVIDER}"
      "suggestion_protobufs"
    )

  @decode_args
  def create_experiment_count_by_org_billing_key(self, organization_id, start_time=None):
    window_start_str = ""
    if start_time is not None:
      start_time = datetime_to_seconds(start_time)
      window_start_str = f"{self.DIVIDER}window_start{self.DIVIDER}{start_time}"
    return self._RedisKey(
      f"experiment_count{self.DIVIDER}organization{self.DIVIDER}{int(organization_id)}{window_start_str}"
    )

  @decode_args
  def create_optimized_run_by_org_billing_key(self, organization_id, start_time=None):
    window_start_str = ""
    if start_time is not None:
      start_time = datetime_to_seconds(start_time)
      window_start_str = f"{self.DIVIDER}window_start{self.DIVIDER}{start_time}"
    return self._RedisKey(
      f"optimized_run_count{self.DIVIDER}organization{self.DIVIDER}{int(organization_id)}{window_start_str}"
    )

  def _assemble_queue_key(self, prefix, suffix, divider):
    assert divider not in prefix
    return self._RedisKey(f"{prefix}{divider}{suffix}")

  @decode_args
  def create_queue_name_key(self, redis_key_prefix, queue_name, divider):
    assert divider not in queue_name
    return self._assemble_queue_key(redis_key_prefix, queue_name, divider)

  @decode_args
  def create_queue_tracking_key(self, queue_name):
    return self._assemble_queue_key(self.QUEUE_TRACKING_PREFIX, queue_name, self.DIVIDER)

  @decode_args
  def create_queue_message_key(self, message_type, group_key, divider):
    return self._assemble_queue_key(message_type, group_key, divider)

  @decode_args
  def create_rate_limit_key(self, rate_limit_type, time, identifier):
    return self._RedisKey(f"rate-limit{self.DIVIDER}{rate_limit_type}{self.DIVIDER}{time}{self.DIVIDER}{identifier}")


class RedisService(Service):
  logger_name = "sigopt.redis"
  SHORT_TIMEOUT = 1.0  # in seconds
  POLLING_TIMEOUT = 30.0  # in seconds

  def __init__(self, services):
    super().__init__(services)
    self.redis = None
    self.blocking_conn_redis = None

  @property
  def enabled(self):
    return self.services.config_broker.get("redis.enabled", True)

  @classmethod
  def _make_redis_tcp(cls, config):
    host = config.get("host")
    port = config.get("port", DEFAULT_REDIS_PORT)
    password = config.get("password", None)
    ssl = config.get("ssl", True)
    ssl_ca_certs = config.get("ssl_ca_certs", None)
    socket_timeout = config.get("socket_timeout")

    ret = redis.Redis(
      host=host,
      port=port,
      ssl=ssl,
      ssl_cert_reqs="required" if ssl_ca_certs else None,
      ssl_ca_certs=ssl_ca_certs,
      password=password,
      socket_connect_timeout=0.5,  # in seconds
      socket_timeout=socket_timeout,
    )
    return ret

  @classmethod
  def _make_redis_unix_socket(cls, config):
    socket_path = config.get("socket_path", DEFAULT_REDIS_SOCKET_PATH)
    socket_timeout = config.get("socket_timeout")
    connection_pool = redis.ConnectionPool(
      connection_class=SigOptUnixDomainSocketConnection,
      path=socket_path,
    )

    ret = redis.Redis(
      connection_pool=connection_pool,
      socket_connect_timeout=0.1,  # in seconds
      socket_timeout=socket_timeout,
    )
    return ret

  @classmethod
  def make_redis(cls, config, **kwargs):
    config = extend_dict({}, config, kwargs)
    mode = config.get("connection_mode", "socket")
    if mode == "socket":
      ret = cls._make_redis_unix_socket(config)
    else:
      assert mode == "tcp"
      ret = cls._make_redis_tcp(config)
    ret.ping()
    return ret

  def get_redis_uri(self):
    mode = self.services.config_broker.get("redis.connection_mode", "socket")
    scheme = "redis"
    if mode == "socket":
      scheme = "redis-socket"
      addr = self.services.config_broker.get("redis.socket_path", DEFAULT_REDIS_SOCKET_PATH)
    else:
      if self.services.config_broker.get("redis.ssl", True):
        scheme = "rediss"
      addr = ":".join(
        str(self.services.config_broker.get(key, default))
        for key, default in (("redis.host", "localhost"), ("redis.port", DEFAULT_REDIS_PORT))
      )
    return f"{scheme}://{addr}"

  def warmup(self):
    if self.enabled:
      try:
        self.redis = self.make_redis(
          self.services.config_broker.get_object("redis"),
          socket_timeout=self.SHORT_TIMEOUT,
        )
        # NOTE: bzpopmin intentionally has a long polling timeout.
        # we want the value to be at least as large as wait_time_seconds, but we don't
        # know which queue this would be called on; we can probably configure it eventually
        self.blocking_conn_redis = self.make_redis(
          self.services.config_broker.get_object("redis"),
          socket_timeout=self.POLLING_TIMEOUT,
        )
      except AssertionError:
        raise
      except Exception:  # pylint: disable=broad-except
        self.redis = None
        self.blocking_conn_redis = None
        self.logger.warning(
          "Unable to connect to Redis at %s",
          self.get_redis_uri(),
        )
    else:
      self.logger.warning("redis disabled")

  @retry_on_failure
  @ensure_redis
  def get(self, redis_key):
    return self.redis.get(self.services.redis_key_service.get_key_value(redis_key))

  @retry_on_failure
  @ensure_redis
  def set(self, redis_key, value, expiry_time=None):
    return self.redis.set(self.services.redis_key_service.get_key_value(redis_key), value=value, ex=expiry_time)

  @ensure_redis
  def increment(self, redis_key):
    return self.redis.incr(self.services.redis_key_service.get_key_value(redis_key))

  @retry_on_failure
  @ensure_redis
  def set_expire_at(self, redis_key, expire_at):
    assert isinstance(expire_at, datetime.datetime)
    return self.redis.expireat(self.services.redis_key_service.get_key_value(redis_key), expire_at)

  @retry_on_failure
  @ensure_redis
  def set_expire(self, redis_key, expire):
    assert isinstance(expire, datetime.timedelta)
    return self.redis.expire(self.services.redis_key_service.get_key_value(redis_key), expire)

  @retry_on_failure
  @ensure_redis
  def exists(self, redis_key):
    exists = self.redis.exists(self.services.redis_key_service.get_key_value(redis_key))
    return bool(exists)

  @retry_on_failure
  @ensure_redis
  def count_sorted_set(self, redis_key):
    return self.redis.zcard(self.services.redis_key_service.get_key_value(redis_key))

  @retry_on_failure
  @ensure_redis
  def count_list(self, redis_key):
    return self.redis.llen(self.services.redis_key_service.get_key_value(redis_key))

  @retry_on_failure
  @ensure_redis
  def add_sorted_set_new(self, redis_key, member_score_tuples):
    return self.redis.zadd(
      self.services.redis_key_service.get_key_value(redis_key),
      dict(member_score_tuples),
      ch=True,
      nx=True,
    )

  @retry_on_failure
  @ensure_redis
  def get_sorted_set_range(self, redis_key, min_index, max_index, reverse=False, withscores=False):
    func = self.redis.zrevrange if reverse else self.redis.zrange
    return func(
      self.services.redis_key_service.get_key_value(redis_key),
      min_index,
      max_index,
      withscores=withscores,
    )

  @retry_on_failure
  @ensure_redis
  def remove_from_sorted_set(self, redis_key, *members):
    if members:
      return self.redis.zrem(self.services.redis_key_service.get_key_value(redis_key), *members)
    return None

  def _validate_timeout(self, timeout):
    if timeout is None or timeout >= self.POLLING_TIMEOUT:
      # NOTE: -1 to allow time for roundtrip communication
      self.services.exception_logger.soft_exception(
        f'timeout "{timeout}" is longer than/equal to socket timeout '
        f"{self.POLLING_TIMEOUT}, using socket_timeout-1 instead"
      )
      timeout = self.POLLING_TIMEOUT - 1
    return max(1, int(timeout))

  @ensure_redis
  def blocking_pop_min_from_sorted_set(self, redis_keys, timeout=None):
    timeout = self._validate_timeout(timeout)
    key_values = [self.services.redis_key_service.get_key_value(rkey) for rkey in redis_keys]
    try:
      # NOTE: returns either single None if nothing popped,
      # or 3-item tuple containing: (RedisKey.key_value, value, score)
      return self.blocking_conn_redis.bzpopmin(key_values, timeout=timeout)
    except redis.exceptions.TimeoutError as e:
      raise RedisServiceTimeoutError(e) from e

  @retry_on_failure
  @ensure_redis
  def list_push(self, redis_key, *members):
    return self.redis.rpush(self.services.redis_key_service.get_key_value(redis_key), *members)

  @ensure_redis
  def blocking_list_pop(self, redis_keys, timeout=None):
    timeout = self._validate_timeout(timeout)
    key_values = [self.services.redis_key_service.get_key_value(rkey) for rkey in redis_keys]
    return self.blocking_conn_redis.blpop(key_values, timeout=timeout)

  @retry_on_failure
  @ensure_redis
  def add_to_set(self, redis_key, *members):
    return self.redis.sadd(self.services.redis_key_service.get_key_value(redis_key), *members)

  @retry_on_failure
  @ensure_redis
  def get_set_members(self, redis_key):
    # Redis cautions that SMEMBERS can be I/O intensive, so we iterate through
    # but recognize there may be race conditions that cause duplicate items
    return distinct(list(self.redis.sscan_iter(self.services.redis_key_service.get_key_value(redis_key))))

  @retry_on_failure
  @ensure_redis
  def set_hash_fields(self, redis_key, mapping):
    return self.redis.hset(self.services.redis_key_service.get_key_value(redis_key), mapping=mapping)

  @retry_on_failure
  @ensure_redis
  def get_all_hash_fields(self, redis_key, length_hint=None):
    # length_hint does NOT affect number of items returned, and can be None
    # but can help speed things up under the hood if set reasonably
    return dict(self.redis.hscan_iter(self.services.redis_key_service.get_key_value(redis_key), count=length_hint))

  @retry_on_failure
  @ensure_redis
  def get_time(self, with_microseconds=False):
    seconds, microseconds = self.redis.time()
    if with_microseconds:
      MICROSECONDS_PER_SECOND = 1e6
      seconds += microseconds / MICROSECONDS_PER_SECOND
    return seconds

  @retry_on_failure
  @ensure_redis
  def remove_from_hash(self, redis_key, *fields):
    return self.redis.hdel(self.services.redis_key_service.get_key_value(redis_key), *fields)

  @retry_on_failure
  def delete(self, redis_key):
    return self.redis.delete(self.services.redis_key_service.get_key_value(redis_key))

  @retry_on_failure
  @ensure_redis
  def dangerously_purge_database(self):
    return self.redis.flushall()
