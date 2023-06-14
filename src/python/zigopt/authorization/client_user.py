# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import deal

from zigopt.authorization.empty import EmptyAuthorization
from zigopt.authorization.user import UserAuthorization
from zigopt.client.model import Client
from zigopt.membership.model import Membership
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.user.model import User


class _BaseClientUserAuthorization(EmptyAuthorization):
  @deal.pre(
    lambda self, current_client, current_user, client_token, current_membership, user_authorization: (
      client_token.client_id == current_client.id
    )
  )
  @deal.pre(
    lambda self, current_client, current_user, client_token, current_membership, user_authorization: (
      user_authorization.scoped_membership is current_membership
    )
  )
  @deal.pre(
    lambda self, current_client, current_user, client_token, current_membership, user_authorization: (
      current_membership.is_owner or user_authorization.scoped_permission
    )
  )
  def __init__(
    self,
    current_client: Client,
    current_user: User,
    client_token,
    current_membership: Membership,
    user_authorization: UserAuthorization,
  ):
    super().__init__()
    self._current_client = current_client
    self._current_membership = current_membership
    self._current_user = current_user
    self._client_token = client_token
    self._user_authorization = user_authorization

  @property
  def current_client(self):
    return self._current_client

  @property
  def current_user(self):
    return self._current_user

  @property
  def api_token(self):
    return self._client_token

  @property
  def developer(self):
    return True

  @property
  def development(self):
    return self.api_token.development or False

  def can_act_on_user(self, services, requested_permission, user):
    return self._user_authorization.can_act_on_user(services, requested_permission, user)

  def can_act_on_token(self, services, requested_permission, token):
    if requested_permission == READ and self._client_token and self._client_token.token == token.token:
      return True
    return bool(
      token
      and self.current_user.id in {token.user_id, token.creating_user_id}
      and self._user_authorization.can_act_on_token(services, requested_permission, token)
    )
