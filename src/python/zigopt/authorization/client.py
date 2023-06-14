# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import deal

from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.client.model import Client
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE
from zigopt.token.model import Token


class ClientAuthorization(EmptyAuthorization):
  @deal.pre(lambda current_client, client_token: client_token.client_id == current_client.id)
  @deal.pre(lambda current_client, client_token: client_token.all_experiments)
  def __init__(self, current_client: Client, client_token: Token):
    super().__init__()
    self._current_client = current_client
    self._client_token = client_token

  @property
  def current_client(self) -> Client:
    return self._current_client

  @property
  def api_token(self) -> Token:
    return self._client_token

  def can_act_on_user(self, services, requested_permission, user):
    return False

  def can_act_on_client(self, services, requested_permission, client):
    return self._can_act_on_client_id(services, requested_permission, client.id)

  def _can_act_on_client_id(self, services, requested_permission, client_id):
    allowed_to_read = (
      self._guest_can_read
      and self.current_client.id is not None
      and client_id is not None
      and (self.current_client.id == client_id)
    )
    if requested_permission == READ:
      return allowed_to_read
    if requested_permission == WRITE:
      return allowed_to_read and self._guest_can_write
    if requested_permission == ADMIN:
      return False
    return False

  def can_act_on_organization(self, services, requested_permission, organization):
    allowed_to_read = (
      self._guest_can_read
      and self.current_client.organization_id is not None
      and organization.id is not None
      and (self.current_client.organization_id == organization.id)
    )
    if requested_permission == READ:
      return allowed_to_read
    if requested_permission in (WRITE, ADMIN):
      return False
    return False

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    return bool(self._can_act_on_client_id(services, requested_permission, client_id))

  def can_act_on_token(self, services, requested_permission, token):
    if requested_permission == READ and self._client_token and self._client_token.token == token.token:
      return True
    return False

  @property
  def _guest_can_read(self):
    return self._client_token.guest_can_read

  @property
  def _guest_can_write(self):
    return self._client_token.guest_can_write
