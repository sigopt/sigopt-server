# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Generator, Sequence

from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import USER_ROLE
from zigopt.invite.model import Invite
from zigopt.json.builder.membership import MembershipJsonBuilder
from zigopt.membership.model import Membership, MembershipType
from zigopt.organization.model import Organization
from zigopt.permission.model import Permission
from zigopt.permission.pending.model import PendingPermission
from zigopt.services.base import Service
from zigopt.user.model import User, get_domain_from_email, normalize_email


class InviteService(Service):
  # pylint: disable=too-many-public-methods
  def create_invite(
    self,
    email: str,
    organization_id: int,
    inviter_id: int,
    invite_code: str,
    membership_type: MembershipType,
    invite_id: int | None = None,
  ) -> Invite:
    return Invite(
      id=invite_id,
      email=email,
      organization_id=organization_id,
      inviter=inviter_id,
      invite_code=invite_code,
      membership_type=membership_type,
      timestamp=current_datetime(),
    )

  def insert_invite(self, invite: Invite) -> Invite:
    self.services.database_service.insert(invite)
    self.services.database_service.flush_session()
    return invite

  def find_by_id(self, invite_id: int) -> Invite | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Invite).filter_by(id=invite_id)
    )

  def find_by_code(self, invite_code: str) -> Invite | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Invite).filter_by(invite_code=invite_code)
    )

  def _query_by_organization_id(self, organization_id: int) -> Query:
    return self.services.database_service.query(Invite).filter(Invite.organization_id == organization_id)

  def find_by_organization_id(self, organization_id: int) -> Sequence[Invite]:
    return self.services.database_service.all(self._query_by_organization_id(organization_id))

  def count_by_organization_id(self, organization_id: int) -> int:
    return self.services.database_service.count(self._query_by_organization_id(organization_id))

  def find_by_email_and_organization(self, email: str, organization_id: int) -> Invite | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Invite)
      .filter(Invite.email == normalize_email(email))
      .filter(Invite.organization_id == organization_id),
    )

  def find_by_email(self, email: str, valid_only: bool) -> Sequence[Invite]:
    invites = self.services.database_service.all(
      self.services.database_service.query(Invite).filter(Invite.email == normalize_email(email)),
    )
    if valid_only:
      invites = self._filter_to_valid_invites(invites)
    return invites

  def delete_by_id(self, invite_id: int) -> int:
    return self.services.database_service.delete_one_or_none(
      self.services.database_service.query(Invite).filter(Invite.id == invite_id)
    )

  def delete_by_organization_id(self, organization_id: int) -> int:
    return self.services.database_service.delete(
      self.services.database_service.query(Invite).filter(Invite.organization_id == organization_id)
    )

  def delete_by_invite_ids(self, invite_ids: Sequence[int]) -> int:
    if invite_ids:
      return self.services.database_service.delete(
        self.services.database_service.query(Invite).filter(Invite.id.in_(invite_ids))
      )
    return 0

  def delete_by_email(self, email: str) -> int:
    return self.services.database_service.delete(
      self.services.database_service.query(Invite).filter(Invite.email == normalize_email(email)),
    )

  def delete_by_email_and_organization(self, email: str, organization_id: int) -> int:
    return self.services.database_service.delete(
      self.services.database_service.query(Invite)
      .filter(Invite.email == normalize_email(email))
      .filter(Invite.organization_id == organization_id),
    )

  # We define a stray invite as one that has 0 associated pending permissions
  def delete_stray_invites_by_organization(self, organization_id: int) -> int:
    stray_invites = (
      self.services.database_service.query(Invite.id)
      .filter(Invite.organization_id == organization_id)
      .outerjoin(PendingPermission)
      .filter(PendingPermission.id.is_(None))
    )
    return self.services.database_service.delete(
      self.services.database_service.query(Invite).filter(Invite.id.in_(stray_invites.subquery())),
    )

  def _can_act_as_organization_owner(self, organization_id: int, inviter: User, inviter_membership: Membership) -> bool:
    if inviter_membership:
      assert inviter_membership.organization_id == organization_id
      assert inviter_membership.user_id == inviter.id
      if inviter_membership.is_owner:
        return True
    return False

  def _inviter_has_permission_to_invite_to_organization(
    self,
    organization_id: int,
    inviter: User,
    inviter_membership: Membership,
    inviter_permissions: Sequence[Permission],
    invitee_intended_membership_type: MembershipType,
    pending_permissions: Sequence[PendingPermission],
  ) -> bool:
    inviter_permissions_by_client = to_map_by_key(inviter_permissions, lambda p: p.client_id)

    if invitee_intended_membership_type == MembershipType.owner:
      return self._can_act_as_organization_owner(
        organization_id=organization_id,
        inviter=inviter,
        inviter_membership=inviter_membership,
      )
    assert invitee_intended_membership_type == MembershipType.member
    # NOTE: An non-owner invite with 0 pending permissions is not valid, because we must confirm that
    # the inviter has permission to administer all the clients on the invite. If there are 0 pending
    # permissions then we will skip important checks
    # TODO: At this time there is no distinction between the authorization required to
    # invite a user to a client and that required to invite them to an org.
    # Organization owners may want to prevent their admins from creating new memberships
    if pending_permissions:
      return all(
        self._inviter_has_permission_to_invite_to_client(
          organization_id=pending_permission.organization_id,
          client_id=pending_permission.client_id,
          inviter=inviter,
          inviter_membership=inviter_membership,
          inviter_permission=inviter_permissions_by_client.get(pending_permission.client_id),
        )
        for pending_permission in pending_permissions
      )
    return False

  def _inviter_has_permission_to_invite_to_client(
    self,
    organization_id: int,
    client_id: int,
    inviter: User,
    inviter_membership: Membership,
    inviter_permission: Permission | None,
  ) -> bool:
    if inviter and inviter_membership:
      assert inviter_membership.user_id == inviter.id

      # If a user is an admin of a team, they are permitted to invite new users into the organization.
      # TODO: Reconsider this, it may make more sense to only let owners create new memberships,
      # but we have existing admins using this functionality
      if inviter_permission:
        assert inviter_permission.user_id == inviter.id
        assert inviter_permission.organization_id == inviter_membership.organization_id
        if inviter_permission.client_id == client_id and inviter_permission.can_admin:
          return True

    if self._can_act_as_organization_owner(
      organization_id=organization_id,
      inviter=inviter,
      inviter_membership=inviter_membership,
    ):
      return True

    return False

  def inviter_can_invite_to_client(
    self, inviter: User, client: Client, organization: Organization, invitee_email: str
  ) -> bool:
    if inviter:
      inviter_membership = self.services.membership_service.find_by_user_and_organization(
        user_id=inviter.id,
        organization_id=client.organization_id,
      )
      if not inviter_membership:
        return False
      inviter_permission = self.services.permission_service.find_by_client_and_user(
        client_id=client.id,
        user_id=inviter.id,
      )
      if self._inviter_has_permission_to_invite_to_client(
        organization_id=client.organization_id,
        client_id=client.id,
        inviter=inviter,
        inviter_membership=inviter_membership,
        inviter_permission=inviter_permission,
      ):
        if self.email_is_permitted_by_organization_for_invite(
          organization=organization,
          email=invitee_email,
          inviter=inviter,
        ):
          return True
    return False

  def invite_is_valid(self, invite: Invite) -> bool:
    return self._filter_to_valid_invites([invite]) == [invite]

  # NOTE: The invite and all pending permissions are valid if the inviter has permission to invite
  # to all the clients that are pending permissions
  # TODO: We require that all pending permissions can be created for this invite to be valid.
  # We could conceivably return "partial" invites where only some of the invites are still valid.
  # This is probably not worth it since it would require that downstream callers take greater care
  # with the invites returned from this method, and is likely a niche use case
  @generator_to_list
  def _filter_to_valid_invites(self, invites: Sequence[Invite]) -> Generator[Invite, None, None]:
    organization_ids = [invite.organization_id for invite in invites]
    inviter_ids = [i.inviter for i in invites]
    inviters = to_map_by_key(self.services.user_service.find_by_ids(inviter_ids), lambda u: u.id)
    inviter_ids = list(inviters.keys())
    memberships = to_map_by_key(
      self.services.membership_service.find_by_users_and_organizations(
        user_ids=inviter_ids,
        organization_ids=organization_ids,
      ),
      lambda m: (m.user_id, m.organization_id),
    )
    permissions = as_grouped_dict(
      self.services.permission_service.find_by_users_and_organizations(
        user_ids=inviter_ids,
        organization_ids=organization_ids,
      ),
      lambda p: p.user_id,
    )
    pending_permissions_by_invite = as_grouped_dict(
      self.services.pending_permission_service.find_by_invite_ids([i.id for i in invites]),
      lambda p: p.invite_id,
    )
    for invite in invites:
      inviter = inviters.get(invite.inviter)
      if not inviter:
        continue
      inviter_membership = memberships.get((invite.inviter, invite.organization_id))
      if not inviter_membership:
        continue
      inviter_permissions = permissions.get(invite.inviter, [])
      pending_permissions = pending_permissions_by_invite.get(invite.id, [])
      if self._inviter_has_permission_to_invite_to_organization(
        organization_id=invite.organization_id,
        inviter=inviter,
        inviter_membership=inviter_membership,
        inviter_permissions=inviter_permissions,
        invitee_intended_membership_type=invite.membership_type,
        pending_permissions=pending_permissions,
      ):
        yield invite

  @generator_to_list
  def create_memberships_and_permissions_from_invites(
    self, user: User, invites: Sequence[Invite], requestor: User
  ) -> Generator[tuple[Membership, Permission, Client], None, None]:
    # pylint: disable=too-many-locals
    invite_ids = [invite.id for invite in invites]
    inviters = to_map_by_key(self.services.user_service.find_by_ids([i.inviter for i in invites]), lambda u: u.id)
    organizations: dict[int, Organization] = to_map_by_key(
      self.services.organization_service.find_by_ids([i.organization_id for i in invites]),
      lambda o: o.id,
    )
    all_pending_permissions = self.services.pending_permission_service.find_by_invite_ids(invite_ids)
    pending_permissions_by_invite = as_grouped_dict(all_pending_permissions, lambda p: p.invite_id)
    client_ids = [pp.client_id for pp in all_pending_permissions]
    clients = to_map_by_key(self.services.client_service.find_by_ids(client_ids), lambda c: c.id)

    # TODO: This filter is extraneous assuming we are passed in valid invites.
    # This filter is moderately expensive so it would be good to remove, though would need
    # to make sure that we have a good way to prevent this from being called on invalid invites
    assert invites == self._filter_to_valid_invites(invites)

    for invite in invites:
      organization = organizations.get(invite.organization_id)
      if not organization:
        continue
      inviter = inviters.get(invite.inviter)
      if self.can_accept_invite_to_organization(user, organization, inviter):
        membership = self.services.membership_service.create_if_not_exists(
          user_id=user.id,
          organization_id=invite.organization_id,
          membership_type=invite.membership_type,
        )
        self.services.iam_logging_service.log_iam(
          requestor=requestor,
          event_name=IamEvent.MEMBERSHIP_CREATE,
          request_parameters={
            "user_id": user.id,
            "membership_type": membership.membership_type.value,
            "organization_id": napply(organization, lambda o: o.id),
          },
          response_element=MembershipJsonBuilder.json(membership, organization, user),
          response_status=IamResponseStatus.SUCCESS,
        )
        for pending_permission in pending_permissions_by_invite.get(invite.id, []):
          client = clients[pending_permission.client_id]
          permission = self.services.permission_service.upsert_from_role(
            invite_role=pending_permission.role,
            client=client,
            user=user,
            requestor=requestor,
          )
          yield (membership, permission, client)

  def eligible_domains_for_direct_signup(self, organization: Organization) -> Sequence[str]:
    return organization.organization_meta.email_domains

  def eligible_domains_for_invite(self, organization: Organization, inviter: User | None) -> Sequence[str]:
    # TODO: Backfill email_domains on organizations and stop falling back to the domain of inviter
    email_domains = organization.organization_meta.email_domains
    if not email_domains and inviter:
      inviter_email = inviter.email
      email_domains = [get_domain_from_email(inviter_email)]
    return email_domains

  def _matches_any_domain_in_list(self, email_domains: Sequence[str], email: str) -> bool:
    assert is_string(email)
    assert is_sequence(email_domains)
    return any(get_domain_from_email(email) == normalize_email(domain) for domain in email_domains)

  def email_is_permitted_by_organization_for_direct_signup(self, organization: Organization, email: str) -> bool:
    email_domains = self.eligible_domains_for_direct_signup(organization)
    return self._matches_any_domain_in_list(email_domains, email)

  def email_is_permitted_by_organization_for_invite(
    self, organization: Organization, email: str, inviter: User | None
  ) -> bool:
    email_domains = self.eligible_domains_for_invite(organization, inviter)
    return self._matches_any_domain_in_list(email_domains, email)

  def _organization_allows_email_signup(self, organization: Organization) -> bool:
    return (
      bool(self.eligible_domains_for_direct_signup(organization))
      and organization.organization_meta.allow_signup_from_email_domains
    )

  def _organization_allows_direct_signup(self, organization: Organization) -> bool:
    return self._organization_allows_email_signup(organization)

  def email_is_permitted_by_client_for_direct_signup(
    self, organization: Organization, client: Client, email: str
  ) -> bool:
    return (
      self.email_is_permitted_by_organization_for_direct_signup(organization=organization, email=email)
      and self._organization_allows_direct_signup(organization=organization)
      and organization.organization_meta.client_for_email_signup == client.id
    )

  def _can_accept_invite_to_organization_by_email(self, user: User, organization: Organization) -> bool:
    if organization:
      return self.services.email_verification_service.has_verified_email_if_needed(user)
    return False

  def can_have_membership_to_organization(self, user: User, organization: Organization) -> bool:
    return self._can_accept_invite_to_organization_by_email(user, organization)

  def can_accept_invite_to_organization(self, user: User, organization: Organization, inviter: User | None) -> bool:
    if (
      user
      and organization
      and self.email_is_permitted_by_organization_for_invite(
        organization=organization, email=user.email, inviter=inviter
      )
    ):
      return self.can_have_membership_to_organization(user=user, organization=organization)
    return False

  def signup_to_organization_if_permitted(self, user: User, organization: Organization) -> Membership | None:
    if organization:
      authorized_by_email = self._organization_allows_email_signup(
        organization
      ) and self._can_accept_invite_to_organization_by_email(user=user, organization=organization)
      if authorized_by_email:
        return self.services.membership_service.create_if_not_exists(
          user_id=user.id,
          organization_id=organization.id,
          membership_type=MembershipType.member,
        )
    return None

  def signup_to_client_if_permitted(
    self, user: User, organization: Organization, client: Client
  ) -> tuple[bool, Permission | None]:
    if (
      organization
      and client
      and self.email_is_permitted_by_client_for_direct_signup(
        organization=organization, client=client, email=user.email
      )
    ):
      membership = self.signup_to_organization_if_permitted(user=user, organization=organization)
      if membership:
        permission = None
        if not membership.is_owner:
          permission = self.services.permission_service.upsert_from_role(
            invite_role=USER_ROLE,
            client=client,
            user=user,
            requestor=user,
          )
        return True, permission
    return False, None
