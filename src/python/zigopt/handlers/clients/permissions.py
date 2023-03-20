# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.clients.base import ClientHandler
from zigopt.json.builder import OwnerPermissionJsonBuilder, PaginationJsonBuilder, PermissionJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ClientsPermissionsHandler(ClientHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    owner_memberships = self.services.membership_service.find_owners_by_organization_id(self.client.organization_id)
    owner_ids = frozenset(m.user_id for m in owner_memberships)
    permissions = self.services.permission_service.find_by_client_id(self.client.id)
    user_ids = set(permission.user_id for permission in permissions)
    user_ids |= owner_ids
    user_ids = list(user_ids)
    users = self.services.user_service.find_by_ids(user_ids)
    user_map = {user.id: user for user in users}

    return PaginationJsonBuilder(
      data=flatten(
        [
          (
            OwnerPermissionJsonBuilder(
              membership=membership,
              user=user_map[membership.user_id],
              client=self.client,
            )
            for membership in owner_memberships
          ),
          (
            PermissionJsonBuilder(
              permission,
              user=user_map[permission.user_id],
              client=self.client,
            )
            for permission in permissions
          ),
        ]
      )
    )
