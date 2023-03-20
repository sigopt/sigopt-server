# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time
from datetime import timedelta

from zigopt.authentication.result import authentication_result
from zigopt.common.non_crypto_random import non_crypto_random
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.net.errors import BadParamError, ForbiddenError, RequestError, UnauthorizedError
from zigopt.user.model import do_password_hash_work_factor_update, password_matches


def right_password(user, password):
  return bool(user and password_matches(password, user.hashed_password))


def right_code(user, code):
  VERIFICATION_THRESHOLD = timedelta(weeks=1).total_seconds()
  now = unix_timestamp()
  return bool(
    user
    and code
    and user.email_verification_timestamp
    and (now - user.email_verification_timestamp) < VERIFICATION_THRESHOLD
    and user.hashed_email_verification_code
    and password_matches(code, user.hashed_email_verification_code)
  )


def authenticate_password(services, user, password):
  app_url = services.config_broker["address.app_url"]
  if right_password(user, password):
    do_password_hash_work_factor_update(services, user, password)
    if services.email_verification_service.has_verified_email_if_needed(user):
      return authentication_result(user=user)
    raise ForbiddenError(f"You must verify your email at {app_url}/verify before you can log in.")
  raise BadParamError("Invalid email/password")


def authenticate_email_code(user, code):
  if right_code(user, code):
    return authentication_result(
      user=user,
      authenticated_from_email_link=True,
    )
  raise BadParamError("Invalid code")


PASSWORD_RESET_EXPIRY_IN_HOURS = 2
PASSWORD_RESET_EXPIRY_IN_SECONDS = timedelta(hours=PASSWORD_RESET_EXPIRY_IN_HOURS).total_seconds()


def authenticate_password_reset_code(services, email, password_reset_code):
  user = services.user_service.find_by_email(email)
  if (
    user
    and user.hashed_password_reset_code
    and user.password_reset_timestamp is not None
    and password_matches(password_reset_code, user.hashed_password_reset_code)
  ):
    if unix_timestamp() - user.password_reset_timestamp < PASSWORD_RESET_EXPIRY_IN_SECONDS:
      return authentication_result(user=user, authenticated_from_email_link=True)
    else:
      raise UnauthorizedError("Expired password_reset_code")
  raise BadParamError("Invalid email/password_reset_code")


DEFAULT_PASSWORD_CHECK_MIN_DELAY_SECONDS = 2
DEFAULT_PASSWORD_CHECK_JITTER_SECONDS = 1


def authenticate_login(services, email, password, code):
  error = None
  start_time = time.time()
  # NOTE: we delay at least 2 because hashing should take ~1s so we need to overestimate
  min_delay_seconds = services.config_broker.get(
    "user.password_check_min_delay_seconds", DEFAULT_PASSWORD_CHECK_MIN_DELAY_SECONDS
  )
  jitter_seconds = services.config_broker.get(
    "user.password_check_jitter_seconds", DEFAULT_PASSWORD_CHECK_JITTER_SECONDS
  )
  delay_seconds_on_failure = min_delay_seconds + jitter_seconds * non_crypto_random.random()
  failure_time = start_time + delay_seconds_on_failure
  try:
    user = services.user_service.find_by_email(email)
    if user:
      # NOTE: If the user cannot auth with a password, we can't reveal the error they have made.
      # This would leak information about the account they are attempting to log in to, notably that
      # the account exists and someone has logged into it successfully.
      # The user must go through the "Forgot Password" flow
      can_auth_with_password = bool(user.hashed_password)
      if can_auth_with_password:
        if password is not None:
          return authenticate_password(services, user, password)
        elif code is not None:
          return authenticate_email_code(user, code)
  except RequestError as request_error:
    error = request_error
  else:
    error = BadParamError("Invalid email/password")
  remaining = max(failure_time - time.time(), 0)
  time.sleep(remaining)
  raise error
