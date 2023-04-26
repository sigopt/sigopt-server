# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.json.builder import OwnerPermissionJsonBuilder, PaginationJsonBuilder, PermissionJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class OrganizationsPermissionsListDetailHandler(OrganizationHandler):
  authenticator = api_token_authentication
  required_permissions = ADMIN

  def handle(self):
    assert self.organization is not None

    owner_memberships = self.services.membership_service.find_owners_by_organization_id(self.organization.id)
    owner_ids = frozenset(m.user_id for m in owner_memberships)

    permissions = self.services.permission_service.find_by_organization_id(self.organization.id)
    unique_user_ids = set(permission.user_id for permission in permissions)
    unique_user_ids |= owner_ids
    user_ids = list(unique_user_ids)
    users = self.services.user_service.find_by_ids(user_ids)
    user_map = {user.id: user for user in users}

    clients = self.services.client_service.find_by_organization_id(self.organization.id)
    client_map = to_map_by_key(clients, lambda c: c.id)

    return PaginationJsonBuilder(
      data=flatten(
        [
          (
            OwnerPermissionJsonBuilder(
              membership=membership,
              user=user_map[membership.user_id],
              client=client,
            )
            for membership in owner_memberships
            for client in clients
          ),
          (
            PermissionJsonBuilder(
              permission,
              user=user_map[permission.user_id],
              client=client_map[permission.client_id],
            )
            for permission in permissions
          ),
        ]
      )
    )
