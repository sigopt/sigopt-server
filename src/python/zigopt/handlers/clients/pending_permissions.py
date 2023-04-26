# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.clients.base import ClientHandler
from zigopt.json.builder import PaginationJsonBuilder, PendingPermissionJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ClientsPendingPermissionsHandler(ClientHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    assert self.auth is not None
    assert self.client is not None

    pending_permissions = self.services.pending_permission_service.find_by_client_id(self.client.id)
    invites = self.services.invite_service.find_by_organization_id(self.client.organization_id)
    invites_map = to_map_by_key(invites, lambda i: i.id)

    return PaginationJsonBuilder(
      data=[
        PendingPermissionJsonBuilder(
          self.auth,
          self.services.config_broker,
          p,
          invites_map[p.invite_id],
          self.client,
        )
        for p in pending_permissions
      ]
    )
