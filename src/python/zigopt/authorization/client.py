# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE


class ClientAuthorization(EmptyAuthorization):
  def __init__(self, current_client, client_token):
    assert client_token.client_id == current_client.id
    super().__init__()
    self._current_client = current_client
    self._client_token = client_token
    assert self._client_token.all_experiments

  @property
  def current_client(self):
    return self._current_client

  @property
  def api_token(self):
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
    elif requested_permission == WRITE:
      return allowed_to_read and self._guest_can_write
    elif requested_permission == ADMIN:
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
    elif requested_permission in (WRITE, ADMIN):
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
