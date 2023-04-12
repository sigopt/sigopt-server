# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import NO_ROLE, permission_to_role
from zigopt.json.builder import MembershipJsonBuilder
from zigopt.membership.model import MembershipType
from zigopt.net.errors import BadParamError, ConflictingDataError


class InviteHandler(Handler):
  def create_invite(
    self,
    email,
    organization,
    membership_type,
    client_invites,
    skip_email,
  ):
    return self._create_invite(
      email,
      organization,
      membership_type,
      client_invites,
      skip_email,
    )

  def update_invite(
    self,
    invite,
    organization,
    membership_type,
    client_invites,
  ):
    invite_id = invite.id
    invite_code = invite.invite_code
    invite_email = invite.email
    self.services.pending_permission_service.delete_by_invite_id(invite_id)
    self.services.invite_service.delete_by_id(invite_id)
    return self._create_invite(
      invite_email,
      organization,
      membership_type,
      client_invites,
      skip_email=True,
      invite_code=invite_code,
      invite_id=invite_id,
    )

  def _create_invite(
    self,
    email,
    organization,
    membership_type,
    client_invites,
    skip_email,
    invite_code=None,
    invite_id=None,
  ):
    # pylint: disable=too-many-locals
    invitee = self.services.user_service.find_by_email(email)
    inviter = self.auth.current_user

    if not self.services.invite_service.email_is_permitted_by_organization_for_invite(organization, email, inviter):
      raise BadParamError(
        "You can only invite users with emails from the following domains:"
        f' {",".join(self.services.invite_service.eligible_domains_for_invite(organization, inviter))}.'
      )

    client_ids = [InviteHandler.get_id_from_client_invite(inv) for inv in client_invites]
    clients = self.services.client_service.find_by_ids(client_ids)
    client_map = to_map_by_key(clients, lambda c: c.id)

    invite_code = invite_code or random_string()

    invite = self.services.invite_service.create_invite(
      email=email,
      organization_id=organization.id,
      inviter_id=inviter.id,
      invite_code=invite_code,
      membership_type=membership_type,
      invite_id=invite_id,
    )

    pending_permissions = []

    if invitee:
      pending_permissions = self.create_pending_permissions(invite, client_invites, client_map, insert=False)
      skip_check = invite_id is not None
      self.update_existing_user(invite, organization, invitee, client_invites, skip_email, skip_check, inviter)
    else:
      if self.services.invite_service.find_by_email_and_organization(invite.email, organization.id):
        raise BadParamError(f"The email address {invite.email} was already invited.")

      self.services.invite_service.insert_invite(invite)
      self.create_pending_permissions(invite, client_invites, client_map, insert=True)
      pending_permissions = self.services.pending_permission_service.find_by_invite_id(invite.id)

      if not skip_email:
        invite_link = self.services.email_templates.accept_invite_link(invite.invite_code, email, organization)
        if invite.membership_type == MembershipType.owner:
          self.send_invite_owner_email(organization, email, invite_link, self.auth.current_user.name)
        else:
          self.send_invite_email(organization, clients, email, invite_link, self.auth.current_user.name)

    return (invite, pending_permissions)

  @classmethod
  def get_updated_client_invites(cls, membership_type, pending_permissions, new_client_invites):
    client_invite_map = dict()
    if membership_type != MembershipType.owner:
      client_invite_map = dict(
        (pp.client_id, dict(id=pp.client_id, role=pp.role, old_role=NO_ROLE)) for pp in pending_permissions
      )
    for client_invite in new_client_invites:
      client_id = InviteHandler.get_id_from_client_invite(client_invite)
      role = InviteHandler.get_role_from_client_invite(client_invite) or NO_ROLE
      old_role = InviteHandler.get_old_role_from_client_invite(client_invite) or NO_ROLE

      old_client_invite = client_invite_map.pop(client_id, {"role": NO_ROLE})
      expected_role = InviteHandler.get_role_from_client_invite(old_client_invite)

      if expected_role and expected_role != old_role:
        raise ConflictingDataError(
          "Current pending permission state out of sync"
          f" - old role `{old_role}` does not match expected role `{expected_role}`"
        )

      if role != NO_ROLE:
        client_invite_map[client_id] = client_invite

    return list(client_invite_map.values())

  def _maybe_check_role_synchonization(self, skip_check, invitee, client_invites):
    if skip_check:
      return

    for client_invite in client_invites:
      invitee_permission = self.services.permission_service.find_by_client_and_user(
        client_id=InviteHandler.get_id_from_client_invite(client_invite),
        user_id=invitee.id,
      )
      expected_role = permission_to_role(invitee_permission)
      old_role = InviteHandler.get_old_role_from_client_invite(client_invite)
      if InviteHandler.get_old_role_from_client_invite(client_invite) != expected_role:
        raise ConflictingDataError(
          f"Current permission state out of sync - old role `{old_role}` does not match expected role `{expected_role}`"
        )

  def _update_current_membership(self, current_membership, invite, invitee, organization):
    # NOTE: Currently only handle elevating members to owners, not the other way around
    if current_membership.membership_type == MembershipType.owner:
      raise BadParamError("Owners cannot have their memberships updated")

    if invite.membership_type == MembershipType.owner:
      self.services.membership_service.elevate_to_owner(current_membership)
      self.services.permission_service.delete_by_organization_and_user(
        organization.id,
        invitee.id,
      )
      self.services.iam_logging_service.log_iam(
        requestor=self.auth.current_user,
        event_name=IamEvent.MEMBERSHIP_UPDATE,
        request_parameters={
          "user_id": invitee.id,
          "membership_type": MembershipType.owner.value,
          "organization_id": organization.id,
        },
        response_element=MembershipJsonBuilder.json(current_membership, organization, invitee),
        response_status=IamResponseStatus.SUCCESS,
      )

  def _create_new_membership(self, invite, invitee, organization):
    membership = self.services.membership_service.insert(
      user_id=invitee.id,
      organization_id=organization.id,
      membership_type=invite.membership_type,
    )
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.MEMBERSHIP_CREATE,
      request_parameters={
        "user_id": invitee.id,
        "membership_type": membership.membership_type.value,
        "organization_id": organization.id,
      },
      response_element=MembershipJsonBuilder.json(membership, organization, invitee),
      response_status=IamResponseStatus.SUCCESS,
    )

  def _send_invite_emails(self, skip_email, invite, invitee, organization, clients):
    if skip_email:
      code = self.services.email_verification_service.set_email_verification_code_without_save(invitee)
      self.services.user_service.update_meta(invitee, invitee.user_meta)
      invite_link = self.services.email_templates.verify_email_link(code, invitee.email)
      if invite.membership_type == MembershipType.owner:
        self.send_reprompt_owner_email(organization, invitee, invite_link)
      else:
        self.send_reprompt_email(organization, clients, invitee, invite_link)
    elif self.services.email_verification_service.has_verified_email_if_needed(invitee):
      self.send_existing_user_invite(invite, organization, clients, invitee)

  def update_existing_user(self, invite, organization, invitee, client_invites, skip_email, skip_check, inviter):
    self._maybe_check_role_synchonization(skip_check, invitee, client_invites)

    client_ids = [InviteHandler.get_id_from_client_invite(inv) for inv in client_invites]
    clients = self.services.client_service.find_by_ids(client_ids)
    client_map = to_map_by_key(clients, lambda c: c.id)

    current_membership = self.services.membership_service.find_by_user_and_organization(invitee.id, organization.id)

    if current_membership or self.services.invite_service.can_accept_invite_to_organization(
      user=invitee,
      organization=organization,
      inviter=inviter,
    ):
      if current_membership:
        self._update_current_membership(current_membership, invite, invitee, organization)
      else:
        self._create_new_membership(invite, invitee, organization)

      for client_invite in client_invites:
        self.services.permission_service.upsert_from_role(
          invite_role=InviteHandler.get_role_from_client_invite(client_invite),
          client=client_map[InviteHandler.get_id_from_client_invite(client_invite)],
          user=invitee,
          requestor=inviter,
        )

      if not skip_email:
        self.send_existing_user_invite(invite, organization, clients, invitee)

    elif self.services.invite_service.find_by_email_and_organization(invite.email, organization.id):
      raise BadParamError(f"The email address {invite.email} was already invited.")

    else:
      self.services.invite_service.insert_invite(invite)
      self.create_pending_permissions(invite, client_invites, client_map, insert=True)

      self._send_invite_emails(skip_email, invite, invitee, organization, clients)

  def send_existing_user_invite(self, invite, organization, clients, invitee):
    if invite.membership_type == MembershipType.owner:
      self.send_invite_owner_existing_user_email(organization, invitee, self.auth.current_user.name)
    else:
      self.send_invite_existing_user_email(organization, clients, invitee, self.auth.current_user.name)

  @staticmethod
  def get_id_from_client_invite(client_invite):
    return int(client_invite["id"])

  @staticmethod
  def get_role_from_client_invite(client_invite):
    return client_invite["role"]

  @staticmethod
  def get_old_role_from_client_invite(client_invite):
    return client_invite["old_role"]

  def send_reprompt_email(self, organization, clients, invitee, invite_link):
    self.services.email_router.send(
      self.services.email_templates.verification_reprompt_email(
        invitee,
        organization,
        clients,
        invite_link,
      )
    )

  def send_reprompt_owner_email(self, organization, invitee, invite_link):
    self.services.email_router.send(
      self.services.email_templates.verification_reprompt_owner_email(
        invitee,
        organization,
        invite_link,
      )
    )

  def send_invite_existing_user_email(self, organization, clients, invitee, inviter):
    self.services.email_router.send(
      self.services.email_templates.invited_existing_email(
        organization,
        clients,
        invitee.email,
        inviter,
      )
    )

  def send_invite_email(self, organization, clients, email, invite_link, inviter):
    self.services.email_router.send(
      self.services.email_templates.invited_email(organization, clients, email, invite_link, inviter)
    )

  def send_invite_owner_existing_user_email(self, organization, invitee, inviter):
    self.services.email_router.send(
      self.services.email_templates.invited_owner_existing_email(
        organization,
        invitee.email,
        inviter,
      )
    )

  def send_invite_owner_email(self, organization, email, invite_link, inviter):
    self.services.email_router.send(
      self.services.email_templates.invited_owner_email(organization, email, invite_link, inviter)
    )

  def create_pending_permissions(self, invite, client_invites, client_map, insert):
    pending_permissions = []
    for client_invite in client_invites:
      client_id = InviteHandler.get_id_from_client_invite(client_invite)
      role = InviteHandler.get_role_from_client_invite(client_invite)
      pending_permission = self.services.pending_permission_service.create_pending_permission(
        invite=invite,
        client=client_map[client_id],
        role=role,
      )
      if insert:
        self.services.pending_permission_service.insert(pending_permission)
      pending_permissions.append(pending_permission)
    return pending_permissions
