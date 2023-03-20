# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.invite.modify import OrganizationsModifyInviteHandler
from zigopt.handlers.validate.base import validate_email
from zigopt.handlers.validate.membership import validate_membership_type
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import InviteJsonBuilder
from zigopt.membership.model import MembershipType


class OrganizationsCreateInviteHandler(OrganizationsModifyInviteHandler):
  Params = ImmutableStruct(
    "Params",
    (
      "email",
      "client_invites",
      "membership_type",
    ),
  )

  def parse_params(self, request):
    data = request.params()
    email = get_with_validation(data, "email", ValidationType.string)
    email = validate_email(email)
    membership_type = (
      get_opt_with_validation(data, "membership_type", ValidationType.string) or MembershipType.member.value
    )
    membership_type = validate_membership_type(membership_type)
    client_invites = OrganizationsModifyInviteHandler.get_client_invites_list_from_json(data)

    return OrganizationsCreateInviteHandler.Params(
      email=email,
      client_invites=client_invites,
      membership_type=membership_type,
    )

  def unpack_params(self, params):
    email, membership_type, client_invites, client_map = OrganizationsModifyInviteHandler.unpack_params(self, params)
    return email, membership_type, client_invites, client_map

  def handle(self, params):
    email, membership_type, client_invites, client_map = self.unpack_params(params)

    self.check_can_invite(
      email=email,
      client_invites=client_invites,
      client_map=client_map,
      membership_type=membership_type,
    )

    (invite, pending_permissions) = self.create_invite(
      email,
      self.organization,
      membership_type,
      client_invites,
      skip_email=False,
    )

    return InviteJsonBuilder.json(
      self.auth,
      self.services.config_broker,
      invite,
      pending_permissions,
      self.organization,
      client_map,
    )
