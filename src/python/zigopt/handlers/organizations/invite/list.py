# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import defaultdict

from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.membership import validate_membership_type
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.invite.model import Invite
from zigopt.json.builder import InviteJsonBuilder, PaginationJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class OrganizationsInvitesListDetailHandler(OrganizationHandler):
  authenticator = api_token_authentication
  # NOTE: ADMIN because normal users on a client in an organization don't need to be
  # able to see who has been invited. Note that team admins can use the /clients/pending_permissions
  # endpoint to view pending permissions in their client
  required_permissions = ADMIN

  Params = ImmutableStruct("Params", ("membership_type",))

  def parse_params(self, request):
    data = request.params()
    membership_type = get_opt_with_validation(data, "membership_type", ValidationType.string)
    membership_type = validate_membership_type(membership_type)
    return self.Params(membership_type)

  def handle(self, params):
    assert self.auth is not None
    assert self.organization is not None

    if params.membership_type:
      invites = self.services.database_service.all(
        self.services.database_service.query(Invite)
        .filter(Invite.organization_id == self.organization.id)
        .filter(Invite.membership_type == params.membership_type)
      )
    else:
      invites = self.services.invite_service.find_by_organization_id(self.organization.id)

    clients = self.services.client_service.find_by_organization_id(self.organization.id)
    pending_permissions = self.services.pending_permission_service.find_by_organization_id(self.organization.id)
    invites_to_pending_permissions_map = defaultdict(list)
    for pp in pending_permissions:
      invites_to_pending_permissions_map[pp.invite_id].append(pp)

    return PaginationJsonBuilder(
      data=[
        InviteJsonBuilder(
          self.auth,
          self.services.config_broker,
          i,
          invites_to_pending_permissions_map[i.id],
          self.organization,
          to_map_by_key(clients, lambda c: c.id),
        )
        for i in invites
      ]
    )
