# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.ratelimit import api_token_rate_limit, login_rate_limit, password_reset_rate_limit
from zigopt.api.request import validate_api_input_string
from zigopt.authentication.login import authenticate_login, authenticate_password_reset_code
from zigopt.authentication.token import authenticate_token
from zigopt.authorization.client import ClientAuthorization
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.authorization.guest import GuestAuthorization
from zigopt.authorization.member import OrganizationMemberAuthorization
from zigopt.authorization.owner import OrganizationOwnerAuthorization
from zigopt.authorization.signup_link import SignupLinkAuthorization
from zigopt.authorization.user import UserAuthorization, UserLoginAuthorization
from zigopt.handlers.validate.base import validate_email
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.net.errors import BadParamError, ForbiddenError, UnauthorizedError
from zigopt.net.responses import TokenStatus

from libsigopt.aux.errors import MissingParamError


def _validate_api_token(token):
  if token is not None:
    return validate_api_input_string(token)
  return token


def helpful_msg(services):
  app_url = services.config_broker["address.app_url"]
  return (
    f"You can find your API Token at {app_url}/tokens/info. API requests "
    "are authenticated using HTTP Basic Auth, with the API token as the username and a blank password. "
    f"Please see {app_url}/docs/overview/authentication for more details."
  )


def _no_token_error(services, request):
  if request.headers and request.headers.get("Authorization") is not None:
    return BadParamError("Could not parse API token. " + helpful_msg(services))
  return UnauthorizedError(
    "No API token provided (we are likely looking for your token in the Authorization header and we can not find it). "
    + helpful_msg(services)
  )


# Authentication methods are staticmethods, so they can be easily put on classes.


def _always_fail_authentication(services, request):
  # Intentionally opaque error message - if we serve this error it likely indicates
  # a coding error where someone forgot to implement `authenticator` on a handler.
  raise ForbiddenError("Authentication failed.")


always_fail_authentication = staticmethod(_always_fail_authentication)


def _no_authentication(services, request):
  return EmptyAuthorization()


no_authentication = staticmethod(_no_authentication)


def _client_token_authentication(services, request):
  """
    Authenticates a client. When used in an api_route, the client is passed
    to the method as the first argument
    """
  maybe_client = _maybe_client_token_authentication(services, request, mandatory=True)
  if not maybe_client.current_client:
    user_agent = request.user_agent.string or ""
    if user_agent.startswith("sigopt-python/"):
      raise ForbiddenError(
        "This endpoint requires a client (team) ID and it was not provided. Provide the client ID to this"
        " endpoint by replacing .experiments() with .clients(CLIENT_ID).experiments()"
      )
    raise ForbiddenError(
      "This endpoint requires a client (team) ID and it was not provided."
      " Provide the client ID to this endpoint by replacing /experiments with /clients/CLIENT_ID/experiments"
    )
  return maybe_client


client_token_authentication = staticmethod(_client_token_authentication)


def _maybe_client_token_authentication(services, request, mandatory=False):
  """
    Authenticates a client, but returns None if there is no token.
    When used in an api_route, the client is passed to the method as the first argument.
    """
  token = _validate_api_token(request.optional_client_token())
  authorization = _do_api_token_authentication(services, request, token, mandatory)
  return authorization


maybe_client_token_authentication = staticmethod(_maybe_client_token_authentication)


def _user_token_authentication(services, request):
  """
    Authenticates a user.
    When used in an api_route, the user is set on the auth object as self.auth.current_user.
    Throws an error if no user is present.
    """
  token = _validate_api_token(request.optional_user_token())
  authorization = _do_api_token_authentication(services, request, token, mandatory=True)
  if not authorization.current_user:
    raise ForbiddenError("The token in use is not associated to any user. " + helpful_msg(services))
  return authorization


user_token_authentication = staticmethod(_user_token_authentication)


def _password_reset_authentication(services, request):
  """
    Authenticates a user when they are resetting their passowrd.
    Uses the password_reset_code parameter to authenticate.
    Also confirms against the API token if available.
    to the method as the first argument.
    """
  email = napply(request.optional_param("email"), validate_email)
  optional_api_token = request.optional_api_token()
  if optional_api_token:
    token = _validate_api_token(request.optional_user_token())
    token_authorization = _do_api_token_authentication(services, request, token, mandatory=True)
    auth_email = token_authorization.current_user and token_authorization.current_user.email
    if auth_email:
      if email and auth_email != email:
        raise BadParamError("Invalid email parameter when authenticating with API token")
      email = auth_email

  if not email:
    raise MissingParamError("email")

  old_plaintext_password = request.optional_param("old_password")
  password_reset_code = request.optional_param("password_reset_code")

  login_xor_pw_reset = bool(optional_api_token) ^ bool(password_reset_code)
  if not login_xor_pw_reset:
    raise BadParamError("Must either login or supply password_reset_code from email")
  if bool(optional_api_token) ^ bool(old_plaintext_password):
    raise BadParamError("old_password only allowed when logged in")

  rate_limit_identifier = password_reset_rate_limit.increment_and_check_rate_limit(services, email)
  if old_plaintext_password:
    authentication = authenticate_login(services, email, old_plaintext_password, code=None)
  else:
    authentication = authenticate_password_reset_code(services, email, password_reset_code)
  password_reset_rate_limit.reset_rate_limit(services, rate_limit_identifier)

  current_user = authentication["user"]
  authenticated_from_email_link = authentication["authenticated_from_email_link"]

  user_token = services.token_service.create_temporary_user_token(current_user.id)
  return UserLoginAuthorization(
    current_user=current_user,
    user_token=user_token,
    authenticated_from_email_link=authenticated_from_email_link,
  )


password_reset_authentication = staticmethod(_password_reset_authentication)


def _api_token_authentication(services, request):
  token = _validate_api_token(request.optional_api_token())
  return _do_api_token_authentication(services, request, token, mandatory=True)


api_token_authentication = staticmethod(_api_token_authentication)


def _do_api_token_authentication(services, request, token, mandatory):
  # pylint: disable=too-many-return-statements
  if token:
    api_token_rate_limit.increment_and_check_rate_limit(services, request)
    authentication = authenticate_token(services, token)
    token_obj = authentication["token"]
    user = authentication["user"]
    client = authentication["client"]
    membership = authentication["membership"]
    permission = authentication["permission"]
    user_authorization = UserAuthorization(
      current_user=user,
      user_token=token_obj,
      scoped_membership=membership,
      scoped_permission=permission,
    )
    if client is not None:
      if user is not None and membership is not None:
        if membership.is_owner:
          if permission is not None:
            services.exception_logger.soft_exception(
              "Owner still has explicit permissions",
              dict(
                user_id=user.id,
                client_id=client.id,
                organization_id=client.organization_id,
                permission_id=permission.id,
              ),
            )
          return OrganizationOwnerAuthorization.construct_from_user_authorization(
            user_authorization=user_authorization,
            current_client=client,
            client_token=token_obj,
            current_membership=membership,
          )
        assert permission is not None
        return OrganizationMemberAuthorization.construct_from_user_authorization(
          user_authorization=user_authorization,
          current_client=client,
          client_token=token_obj,
          current_membership=membership,
          current_permission=permission,
        )
      assert user is None and permission is None and membership is None
      if token_obj.all_experiments:
        return ClientAuthorization(current_client=client, client_token=token_obj)
      if token_obj.guest_can_read:
        return GuestAuthorization(current_client=client, client_token=token_obj)
      return SignupLinkAuthorization(current_client=client, client_token=token_obj)
    if user is not None:
      return user_authorization

    raise ForbiddenError(
      "This endpoint requires a valid API token. " + helpful_msg(services),
      token_status=TokenStatus.REVOKED,
    )
  if mandatory:
    raise _no_token_error(services, request)
  return EmptyAuthorization()


def _login_authentication(services, request):
  code = request.optional_param("code")
  email = validate_email(request.required_param("email"))
  password = request.optional_param("password")

  try:
    # We allow the user to log in with either their password or their email verification
    # code. It's safe to log the user in with the code, because they have already established that they
    # control the email address. Thus, they could just reset the password.
    if password is not None and code is not None:
      raise BadParamError("Cannot provide both password and code parameters.")

    rate_limit_identifier = login_rate_limit.increment_and_check_rate_limit(services, request)
    authentication = authenticate_login(services, email, password, code)
    login_rate_limit.reset_rate_limit(services, rate_limit_identifier)
    user = authentication["user"]
    if user is not None:
      authenticated_from_email_link = authentication["authenticated_from_email_link"]
      user_token = services.token_service.create_temporary_user_token(user.id)
      return UserLoginAuthorization(
        current_user=user,
        user_token=user_token,
        authenticated_from_email_link=authenticated_from_email_link,
      )
    # NOTE: shouldn't be able to get here, but this future-proofs it
    raise BadParamError("Invalid email/password")
  except Exception:
    services.iam_logging_service.log_iam_log_in(
      event_name=IamEvent.USER_LOG_IN,
      request_parameters={"identifier": email},
      response_element={},
      response_status=IamResponseStatus.FAILURE,
    )
    raise


login_authentication = staticmethod(_login_authentication)
