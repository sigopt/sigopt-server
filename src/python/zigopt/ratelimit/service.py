# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime as dt

from zigopt.common import *
from zigopt.services.base import Service


LOGIN_RATE_LIMIT = "login"
API_TOKEN_NON_MUTATING_RATE_LIMIT = "token-non-mutating"
API_TOKEN_MUTATING_RATE_LIMIT = "token-mutating"
OBJECT_ENUMERATION_RATE_LIMIT = "object-enumeration"


TEN_MINUTES_IN_SECONDS = 60 * 10


class RateLimiter(Service):
  @property
  def enabled(self):
    return self.services.config_broker.get("ratelimit.enabled", True)

  def _get_value(self, config_key, default):
    return self.services.config_broker.get(config_key, default)

  @property
  def login_max_attempts(self):
    return self._get_value(
      config_key="ratelimit.login.max_attempts",
      default=5,
    )

  @property
  def login_window_length_seconds(self):
    return self._get_value(
      config_key="ratelimit.login.window_length",
      default=TEN_MINUTES_IN_SECONDS,
    )

  @property
  def token_non_mutating_max_attempts(self):
    return self._get_value(
      config_key="ratelimit.token_non_mutating.max_attempts",
      default=100,
    )

  @property
  def token_non_mutating_window_length_seconds(self):
    return self._get_value(
      config_key="ratelimit.token_non_mutating.window_length",
      default=1,
    )

  @property
  def token_mutating_max_attempts(self):
    return self._get_value(
      config_key="ratelimit.token_mutating.max_attempts",
      default=50,
    )

  @property
  def token_mutating_window_length_seconds(self):
    return self._get_value(
      config_key="ratelimit.token_mutating.window_length",
      default=1,
    )

  @property
  def object_enumeration_max_attempts(self):
    return self._get_value(
      config_key="ratelimit.object_enumeration.max_attempts",
      default=10,
    )

  @property
  def object_enumeration_window_length_seconds(self):
    return self._get_value(
      config_key="ratelimit.object_enumeration.window_length",
      default=TEN_MINUTES_IN_SECONDS,
    )

  def max_attempts(self, rate_limit_type):
    return {
      LOGIN_RATE_LIMIT: self.login_max_attempts,
      API_TOKEN_NON_MUTATING_RATE_LIMIT: self.token_non_mutating_max_attempts,
      API_TOKEN_MUTATING_RATE_LIMIT: self.token_mutating_max_attempts,
      OBJECT_ENUMERATION_RATE_LIMIT: self.object_enumeration_max_attempts,
    }[rate_limit_type]

  def window_length_seconds(self, rate_limit_type):
    return {
      LOGIN_RATE_LIMIT: self.login_window_length_seconds,
      API_TOKEN_NON_MUTATING_RATE_LIMIT: self.token_non_mutating_window_length_seconds,
      API_TOKEN_MUTATING_RATE_LIMIT: self.token_mutating_window_length_seconds,
      OBJECT_ENUMERATION_RATE_LIMIT: self.object_enumeration_window_length_seconds,
    }[rate_limit_type]

  def _get_snapped_time(self, rate_limit_type):
    now = self.services.redis_service.get_time()
    window_length = self.window_length_seconds(rate_limit_type)
    return now - (now % window_length)

  def _key(self, rate_limit_type, identifier, time):
    return self.services.redis_key_service.create_rate_limit_key(rate_limit_type, identifier, time)

  def still_within_rate_limit(self, rate_limit_type, identifier, increment=True):
    time = self._get_snapped_time(rate_limit_type)
    key = self._key(rate_limit_type, identifier, time)
    if increment:
      count = self.services.redis_service.increment(key)
    else:
      count = napply(self.services.redis_service.get(key), int) or 0
    expiry = 2 * dt.timedelta(seconds=self.window_length_seconds(rate_limit_type))
    self.services.redis_service.set_expire(key, expiry)
    max_attempts = self.max_attempts(rate_limit_type)
    return count <= max_attempts

  def clear_rate_limit(self, rate_limit_type, identifier):
    time = self._get_snapped_time(rate_limit_type)
    key = self._key(rate_limit_type, identifier, time)
    self.services.redis_service.delete(key)
