# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import deal

from zigopt.authentication.result import (
  AuthenticationResult,
  ClientAuthenticationResult,
  OrganizationAuthenticationResult,
)
from zigopt.net.errors import ForbiddenError
from zigopt.net.responses import TokenStatus
from zigopt.token.model import Token


@deal.raises(ForbiddenError, TypeError)
def authenticate_token(services, token: str) -> AuthenticationResult:
  token_obj = services.token_service.find_by_token(token, include_expired=True)
  if token_obj is None:
    return AuthenticationResult()
  if token_obj.expired:
    raise ForbiddenError("Your API token has expired.", token_status=TokenStatus.EXPIRED)
  if token_obj.is_client_token:
    return authenticate_client_token(services, token_obj)
  if token_obj.is_user_token:
    return authenticate_user_token(services, token_obj)
  raise TypeError("Token is of invalid type")


@deal.raises(ForbiddenError)
def authenticate_client_token(services, token_obj: Token | None) -> AuthenticationResult:
  if token_obj and token_obj.client_id:
    client = services.client_service.find_by_id(token_obj.client_id, include_deleted=True)
    if client:
      if client.deleted:
        raise ForbiddenError(f"Client {client.id} has been deleted")
      if token_obj.user_id is not None:
        membership = services.membership_service.find_by_user_and_organization(
          user_id=token_obj.user_id,
          organization_id=client.organization_id,
        )
        if membership is not None:
          permission = services.permission_service.find_by_client_and_user(token_obj.client_id, token_obj.user_id)
          if permission is not None and permission.can_read or membership.is_owner:
            user = services.user_service.find_by_id(token_obj.user_id, include_deleted=True)
            if user.deleted:
              raise ForbiddenError(f"User {user.id} has been deleted")
            return AuthenticationResult(
              token=token_obj,
              user=user,
              client_authentication_result=ClientAuthenticationResult(client=client, permission=permission),
              organization_authentication_result=OrganizationAuthenticationResult(membership=membership),
            )
      else:
        return AuthenticationResult(
          token=token_obj, client_authentication_result=ClientAuthenticationResult(client=client)
        )
  return AuthenticationResult()


@deal.raises(ForbiddenError)
def authenticate_user_token(services, token_obj: Token | None) -> AuthenticationResult:
  if token_obj and token_obj.user_id:
    user = services.user_service.find_by_id(token_obj.user_id, include_deleted=True)
    if user:
      if user.deleted:
        raise ForbiddenError(f"User {user.id} has been deleted")
      return AuthenticationResult(token=token_obj, user=user)
  return AuthenticationResult()
