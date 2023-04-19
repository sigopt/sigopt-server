# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.handlers.base.invite import InviteHandler
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.validate.base import validate_email
from zigopt.handlers.validate.role import validate_role
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import NO_ROLE
from zigopt.json.builder import PendingPermissionJsonBuilder
from zigopt.membership.model import MembershipType
from zigopt.net.errors import ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN

from libsigopt.aux.errors import InvalidValueError, SigoptValidationError


class BaseSetPermissionHandler(ClientHandler):
  def check_can_set(self, user_id, invite_role):
    assert self.auth is not None
    assert self.client is not None

    validate_role(invite_role)

    if user_id == self.auth.current_user.id:
      raise SigoptValidationError("You cannot modify your own role")

    if self.services.membership_service.user_is_owner_for_organization(
      user_id=user_id,
      organization_id=self.client.organization_id,
    ):
      raise SigoptValidationError("The role of the client's owner cannot be modified.")


class ClientsCreateInviteHandler(BaseSetPermissionHandler, InviteHandler):
  authenticator = user_token_authentication

  # NOTE: We allow client admins users to invite other members to join the org,
  # even if they are not organization owners.
  required_permissions = ADMIN

  def parse_params(self, request):
    return request

  def handle(self, request):
    # pylint: disable=too-many-locals
    assert self.auth is not None
    assert self.client is not None
    client = self.client

    data = request.params()
    email = validate_email(get_with_validation(data, "email", ValidationType.string))
    old_role = validate_role(get_opt_with_validation(data, "old_role", ValidationType.string) or NO_ROLE)
    role = validate_role(get_with_validation(data, "role", ValidationType.string))
    skip_email = get_opt_with_validation(data, "skip_email", ValidationType.boolean)

    invitee = self.services.user_service.find_by_email(email)
    self.check_can_set(user_id=invitee.id if invitee else None, invite_role=role)
    organization = self.services.organization_service.find_by_id(client.organization_id)

    # TODO(SN-1085): More granular error messages here
    if not self.services.invite_service.inviter_can_invite_to_client(
      inviter=self.auth.current_user,
      client=client,
      organization=organization,
      invitee_email=email,
    ):
      raise ForbiddenError("You do not have permission to invite this email address.")

    client_invites = [dict(id=client.id, role=role, old_role=old_role)]
    existing_invite = self.services.invite_service.find_by_email_and_organization(email, client.organization_id)

    if existing_invite:
      if existing_invite.membership_type == MembershipType.owner:
        raise InvalidValueError("This email was already invited as an owner")

      existing_pending_permissions = self.services.pending_permission_service.find_by_invite_id(existing_invite.id)
      new_client_invites = InviteHandler.get_updated_client_invites(
        existing_invite.membership_type,
        existing_pending_permissions,
        client_invites,
      )
      invite, pending_permissions = self.update_invite(
        existing_invite,
        organization,
        existing_invite.membership_type,
        new_client_invites,
      )
      pending_permission = find(pending_permissions, lambda pp: pp.client_id == client.id)

    else:
      (invite, pending_permissions) = self.create_invite(
        email, organization, MembershipType.member, client_invites, skip_email
      )

      assert len(pending_permissions) == 1
      (pending_permission,) = pending_permissions

    return PendingPermissionJsonBuilder.json(
      self.auth,
      self.services.config_broker,
      pending_permission,
      invite,
      client,
    )


class ClientsUninviteHandler(BaseSetPermissionHandler):
  authenticator = user_token_authentication

  def parse_params(self, request):
    data = request.params()
    return validate_email(get_with_validation(data, "email", ValidationType.string))

  def handle(self, email):
    assert self.auth is not None
    assert self.client is not None

    invitee = self.services.user_service.find_by_email(email)
    self.check_can_set(user_id=invitee.id if invitee else None, invite_role=None)

    if invitee:
      self.services.permission_service.delete_by_client_and_user(self.client.id, invitee.id)
      self.services.iam_logging_service.log_iam(
        requestor=self.auth.current_user,
        event_name=IamEvent.PERMISSION_DELETE,
        request_parameters={
          "user_id": invitee.id,
          "client_id": self.client.id,
        },
        response_element={},
        response_status=IamResponseStatus.SUCCESS,
      )
      num_permissions = self.services.permission_service.count_by_organization_and_user(
        self.client.organization_id, invitee.id
      )
      if num_permissions == 0:
        self.services.membership_service.delete_by_organization_and_user(self.client.organization_id, invitee.id)
        self.services.iam_logging_service.log_iam(
          requestor=self.auth.current_user,
          event_name=IamEvent.MEMBERSHIP_DELETE,
          request_parameters={
            "user_id": invitee.id,
            "organization_id": self.client.organization_id,
          },
          response_element={},
          response_status=IamResponseStatus.SUCCESS,
        )

    self.services.pending_permission_service.delete_by_email_and_client(email, self.client)
    invite = self.services.invite_service.find_by_email_and_organization(email, self.client.organization_id)
    if invite:
      num_pending_permissions = self.services.pending_permission_service.count_by_invite_id(invite.id)
      if num_pending_permissions == 0:
        self.services.invite_service.delete_by_email_and_organization(email, self.client.organization_id)
    return {}
