# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.invite import InviteHandler
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.membership import validate_membership_type
from zigopt.handlers.validate.role import validate_invite_role, validate_role
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.invite.constant import NO_ROLE
from zigopt.invite.model import Invite
from zigopt.membership.model import MembershipType
from zigopt.net.errors import BadParamError, ForbiddenError
from zigopt.permission.pending.model import PendingPermission
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class OrganizationsModifyInviteHandler(OrganizationHandler, InviteHandler):
  authenticator = user_token_authentication
  required_permissions = ADMIN

  Params = ImmutableStruct(
    "Params",
    (
      "email",
      "client_invites",
      "membership_type",
    ),
  )

  invite: Invite
  pending_permissions: list[PendingPermission]

  def parse_params(self, request):
    data = request.params()

    if "email" in data and get_with_validation(data, "email", ValidationType.string) != self.invite.email:
      raise BadParamError("You cannot modify the email of an existing invite")

    email = self.invite.email

    membership_type = self.invite.membership_type
    if "membership_type" in data:
      membership_type = get_opt_with_validation(data, "membership_type", ValidationType.string)
      membership_type = validate_membership_type(membership_type)

    new_client_invites = OrganizationsModifyInviteHandler.get_client_invites_list_from_json(data, validate_role)
    updated_client_invites = InviteHandler.get_updated_client_invites(
      membership_type,
      self.pending_permissions,
      new_client_invites,
    )

    if membership_type == MembershipType.owner and updated_client_invites:
      raise BadParamError("You cannot invite an owner to specific clients")

    if membership_type != MembershipType.owner and not updated_client_invites:
      raise BadParamError("The member invite must have at least one client")

    return OrganizationsModifyInviteHandler.Params(
      email=email,
      client_invites=updated_client_invites,
      membership_type=membership_type,
    )

  def unpack_params(self, params):
    email = params.email
    membership_type = params.membership_type or MembershipType.member
    client_invites = params.client_invites

    clients = self.services.client_service.find_by_organization_id(self.organization.id)
    client_map = to_map_by_key(clients, lambda c: c.id)

    return email, membership_type, client_invites, client_map

  @staticmethod
  def get_client_invites_list_from_json(data, role_validation=validate_invite_role):
    client_invites = (
      get_opt_with_validation(data, "client_invites", ValidationType.arrayOf(ValidationType.object)) or []
    )
    return [
      dict(
        id=get_with_validation(client_invite, "id", ValidationType.integer_string),
        role=role_validation(get_with_validation(client_invite, "role", ValidationType.string)),
        old_role=role_validation(get_opt_with_validation(client_invite, "old_role", ValidationType.string)) or NO_ROLE,
      )
      for client_invite in client_invites
    ]

  def check_can_invite(self, email, client_invites, client_map, membership_type, skip_existing=False):
    invitee = self.services.user_service.find_by_email(email)

    if any(InviteHandler.get_id_from_client_invite(invite) not in client_map for invite in client_invites):
      raise BadParamError(f"Some of the clients aren't in the {self.organization.name} organization")

    if membership_type != MembershipType.owner and not client_invites:
      raise BadParamError("The invitee must be invited to at least 1 client if they are not being invited as an owner")

    if membership_type == MembershipType.owner and client_invites:
      raise BadParamError("The invitee must not be invited to any clients if they are being invited as an owner")

    if not skip_existing:
      existing_invite = self.services.invite_service.find_by_email_and_organization(email, self.organization.id)
      if existing_invite:
        raise BadParamError("This email address was already invited.")

    if invitee and invitee.id == self.auth.current_user.id:
      raise BadParamError("You cannot modify your own role")

    invite_membership = self.services.membership_service.find_by_user_and_organization(
      self.auth.current_user.id,
      self.organization_id,
    )

    if invite_membership is None or not invite_membership.is_owner:
      raise ForbiddenError("You do not have permissions to invite to this organization.")
