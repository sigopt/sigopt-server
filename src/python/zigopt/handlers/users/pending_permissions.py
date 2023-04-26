# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.users.base import UserHandler
from zigopt.json.builder import PaginationJsonBuilder, PendingPermissionJsonBuilder


class UsersPendingPermissionsHandler(UserHandler):
  authenticator = api_token_authentication

  def handle(self):
    assert self.auth is not None
    assert self.user is not None

    invites = self.services.invite_service.find_by_email(self.user.email, valid_only=True)
    invite_map = to_map_by_key(invites, lambda i: i.id)
    invite_ids = list(invite_map.keys())
    pending_permissions = self.services.pending_permission_service.find_by_invite_ids(invite_ids)
    client_ids = [pp.client_id for pp in pending_permissions]
    clients = self.services.client_service.find_by_ids(client_ids)
    client_map = to_map_by_key(clients, lambda c: c.id)
    return PaginationJsonBuilder(
      data=[
        PendingPermissionJsonBuilder(
          self.auth,
          self.services.config_broker,
          pending_permission,
          invite_map[pending_permission.invite_id],
          client_map[pending_permission.client_id],
        )
        for pending_permission in pending_permissions
        if pending_permission.client_id in client_map
      ]
    )
