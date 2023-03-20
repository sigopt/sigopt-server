# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE, READ


def readonly(func):
  def wrapped(self, services, requested_permission, *args, **kwargs):
    if requested_permission in (READ, NONE):
      return func(self, services, requested_permission, *args, **kwargs)
    return False

  return wrapped


class SignupLinkAuthorization(EmptyAuthorization):
  def __init__(self, current_client, client_token):
    assert client_token.client_id == current_client.id
    super().__init__()
    self._current_client = current_client
    self._client_token = client_token

  @property
  def current_client(self):
    return self._current_client

  @property
  def api_token(self):
    return self._client_token

  @readonly
  def can_act_on_client(self, services, requested_permission, client):
    return self._can_act_on_client_id(services, requested_permission, client.id)

  def _can_act_on_client_id(self, services, requested_permission, client_id):
    return (
      self._client_token.guest_can_read
      and self._current_client.id
      and client_id
      and self._current_client.id == client_id
    )

  @readonly
  def can_act_on_organization(self, services, requested_permission, organization):
    return (
      self._client_token.guest_can_read
      and self._current_client.id
      and organization
      and organization.id
      and self._current_client.organization_id == organization.id
    )
