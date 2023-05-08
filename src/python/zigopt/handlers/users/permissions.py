# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import defaultdict

from zigopt.common import *
from zigopt.api.auth import api_token_authentication, user_token_authentication
from zigopt.client.model import Client
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.users.base import UserHandler
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import OwnerPermissionJsonBuilder, PaginationJsonBuilder, PermissionJsonBuilder
from zigopt.net.errors import ForbiddenError


class UsersPermissionsHandler(UserHandler):
  authenticator = api_token_authentication

  Params = ImmutableStruct("Params", ("organization",))

  def parse_params(self, request):
    data = request.params()
    organization_id = get_opt_with_validation(data, "organization", ValidationType.id)
    organization = None
    if organization_id:
      organization = self.services.organization_service.find_by_id(organization_id)
    return self.Params(organization=organization)

  def handle(self, params):
    assert self.user is not None

    owner_memberships = self.services.membership_service.find_owners_by_user_id(self.user.id)
    owned_organization_ids = frozenset(membership.organization_id for membership in owner_memberships)
    permissions = sorted(self.services.permission_service.find_by_user_id(self.user.id), key=lambda x: x.id)

    client_ids = [permission.client_id for permission in permissions]
    clients = self.services.client_service.find_by_ids_or_organization_ids(client_ids, list(owned_organization_ids))
    client_id_map = to_map_by_key(clients, lambda c: c.id)
    client_org_id_map = defaultdict(list)
    for client in clients:
      client_org_id_map[client.organization_id].append(client)

    if params.organization:
      owner_memberships = [m for m in owner_memberships if m.organization_id == params.organization.id]
      permissions = [p for p in permissions if p.organization_id == params.organization.id]

    return PaginationJsonBuilder(
      data=[
        *(
          OwnerPermissionJsonBuilder(
            membership=membership,
            client=client,
            user=self.user,
          )
          for membership in owner_memberships
          for client in client_org_id_map[membership.organization_id]
        ),
        *(
          PermissionJsonBuilder(
            permission,
            client=client_id_map[permission.client_id],
            user=self.user,
          )
          for permission in permissions
          if permission.organization_id not in owned_organization_ids and permission.client_id in client_id_map
        ),
      ]
    )


class UsersRequestPermissionsHandler(UserHandler):
  authenticator = user_token_authentication

  def parse_params(self, request):
    client_id = get_with_validation(request.params(), "client", ValidationType.id)
    return client_id

  def handle(self, client_id):
    if not self.services.email_verification_service.has_verified_email_if_needed(self.user):
      raise ForbiddenError("You must verify your email")
    client: Client | None = self.services.client_service.find_by_id(client_id)
    organization = napply(client, lambda c: self.services.organization_service.find_by_id(c.organization_id))
    could_signup, _ = self.services.invite_service.signup_to_client_if_permitted(
      user=self.user,
      organization=organization,
      client=client,
    )
    if could_signup:
      # NOTE: Since the `permission` could be None (if the user is an org owner),
      # we just never return anything to avoid writing code that depends on a permission
      # always being returned.
      return {}
    raise ForbiddenError("You are not authorized to join this client")
