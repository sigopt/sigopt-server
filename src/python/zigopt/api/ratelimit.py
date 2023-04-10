# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math

from zigopt.handlers.validate.base import validate_email
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.net.errors import TooManyRequestsError
from zigopt.ratelimit.service import API_TOKEN_MUTATING_RATE_LIMIT, API_TOKEN_NON_MUTATING_RATE_LIMIT, LOGIN_RATE_LIMIT


_UNUSED = object()
EMAIL_IDENTIFIER = "email"
TOKEN_IDENTIFIER = "token"


class _BaseRateLimit(object):
  def _on_raise(self, services, identifier, identifier_type):
    return None

  def _check_rate_limit(self, services, identifying_object, rate_limit_type, increment=True):
    identifier, identifier_type = self._get_identifier(services, identifying_object)
    if services.rate_limiter.enabled and identifier != _UNUSED:
      if not services.rate_limiter.still_within_rate_limit(
        rate_limit_type,
        identifier,
        increment,
      ):
        msg = self._on_raise(services, identifier, identifier_type) or ""
        raise TooManyRequestsError(f"Your account has been temporarily disabled because of too many requests.{msg}")
    return identifier

  def increment_and_check_rate_limit(self, services, identifying_object):
    raise NotImplementedError()

  def reset_rate_limit(self, services, identifier):
    raise NotImplementedError()


class _LoginRateLimit(_BaseRateLimit):
  def _on_raise(self, services, identifier, identifier_type):
    services.iam_logging_service.log_iam_no_requestor(
      event_name=IamEvent.USER_LOG_IN_RATE_LIMIT,
      request_parameters={"identifier": identifier},
      response_element={
        "failed_attempts": services.rate_limiter.login_max_attempts,
        "ratelimit_window_length": services.rate_limiter.login_window_length_seconds,
      },
      response_status=IamResponseStatus.SUCCESS,
    )
    if identifier_type == EMAIL_IDENTIFIER:
      if services.user_service.find_by_email(identifier):
        services.email_router.send(services.email_templates.login_ratelimit(identifier))

    minutes = math.ceil(services.rate_limiter.login_window_length_seconds / 60)
    return f" Please wait {minutes} minutes before trying to log in again."

  def _get_identifier(self, services, identifying_object):
    return validate_email(identifying_object.required_param("email")), EMAIL_IDENTIFIER

  def increment_and_check_rate_limit(self, services, identifying_object):
    return self._check_rate_limit(services, identifying_object, LOGIN_RATE_LIMIT)

  def reset_rate_limit(self, services, identifier):
    if services.rate_limiter.enabled and identifier is not _UNUSED:
      services.rate_limiter.clear_rate_limit(LOGIN_RATE_LIMIT, identifier)


login_rate_limit = _LoginRateLimit()


# NOTE: intentionally use same rate limit key as LOGIN_RATE_LIMIT, since they're both password-checking related
class _PasswordResetRateLimit(_LoginRateLimit):
  def _get_identifier(self, services, identifying_object):
    return validate_email(identifying_object), EMAIL_IDENTIFIER


password_reset_rate_limit = _PasswordResetRateLimit()


class _ApiTokenRateLimit(_BaseRateLimit):
  NON_MUTATING_METHODS = {"GET", "HEAD", "OPTIONS"}

  def _get_identifier(self, services, identifying_object):
    token = identifying_object.optional_client_token()
    if token is not None:
      return token, TOKEN_IDENTIFIER
    return _UNUSED, _UNUSED

  def _on_raise(self, services, identifier, identifier_type):
    return " Please wait a few minutes and try again more slowly."

  def _rate_limit_type(self, identifying_object):
    rate_limit_type = API_TOKEN_MUTATING_RATE_LIMIT
    if identifying_object.method in self.NON_MUTATING_METHODS:
      rate_limit_type = API_TOKEN_NON_MUTATING_RATE_LIMIT
    return rate_limit_type

  def increment_and_check_rate_limit(self, services, identifying_object):
    rate_limit_type = self._rate_limit_type(identifying_object)
    return self._check_rate_limit(services, identifying_object, rate_limit_type)

  def reset_rate_limit(self, services, identifier):
    raise Exception("API RateLimit should not get reset")


api_token_rate_limit = _ApiTokenRateLimit()
