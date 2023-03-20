# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.invite.constant import ADMIN_ROLE, USER_ROLE
from zigopt.membership.model import MembershipType

from integration.auth import AuthProvider
from integration.service.test_base import ServiceBase


class TestInviteLogic(ServiceBase):
  def test_organization_owner_can_invite(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    self.make_membership(services, normal_user, organization, is_owner=True)
    client = self.make_client(services, "Test Client 1", organization)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@notsigopt.ninja",
      organization=organization,
      inviter=normal_user,
      membership_type=MembershipType.owner,
    )
    inviter = services.user_service.find_by_id(invite.inviter)
    assert services.invite_service.inviter_can_invite_to_client(inviter, client, organization, invite.email)

  def test_cant_invite_wrong_email(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    self.make_membership(services, normal_user, organization, is_owner=True)
    client = self.make_client(services, "Test Client 1", organization)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@somefakedomain.com",
      organization=organization,
      inviter=normal_user,
      membership_type=MembershipType.owner,
    )
    inviter = services.user_service.find_by_id(invite.inviter)
    assert not services.invite_service.inviter_can_invite_to_client(inviter, client, organization, invite.email)

  def test_client_admin_can_invite(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    services.membership_service.insert(normal_user.id, organization.id)
    client = self.make_client(services, "Test Client 1", organization)
    self.make_permission(services, normal_user, client, ADMIN_ROLE)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@notsigopt.ninja",
      organization=organization,
      inviter=normal_user,
      membership_type=MembershipType.owner,
    )
    inviter = services.user_service.find_by_id(invite.inviter)
    assert services.invite_service.inviter_can_invite_to_client(inviter, client, organization, invite.email)

  def test_normal_user_cant_invite(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    services.membership_service.insert(normal_user.id, organization.id)
    client = self.make_client(services, "Test Client 1", organization)
    self.make_permission(services, normal_user, client, USER_ROLE)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@notsigopt.ninja",
      organization=organization,
      inviter=normal_user,
      membership_type=MembershipType.owner,
    )
    inviter = services.user_service.find_by_id(invite.inviter)
    assert not services.invite_service.inviter_can_invite_to_client(inviter, client, organization, invite.email)

  def test_admin_on_other_team_cant_invite(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    services.membership_service.insert(normal_user.id, organization.id)
    client1 = self.make_client(services, "Test Client 1", organization)
    client2 = self.make_client(services, "Test Client 2", organization)
    self.make_permission(services, normal_user, client1, ADMIN_ROLE)
    self.make_permission(services, normal_user, client2, USER_ROLE)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@notsigopt.ninja",
      organization=organization,
      inviter=normal_user,
      membership_type=MembershipType.owner,
    )
    inviter = services.user_service.find_by_id(invite.inviter)
    assert not services.invite_service.inviter_can_invite_to_client(inviter, client2, organization, invite.email)

  def test_invite_validity(self, services, normal_user):
    email = AuthProvider.randomly_generated_email()
    organization = self.make_organization(services, "Test Organization")
    membership = services.membership_service.insert(
      normal_user.id,
      organization.id,
      membership_type=MembershipType.owner,
    )
    client = self.make_client(services, "Test Client", organization)
    self.make_permission(services, normal_user, client, ADMIN_ROLE)
    self.make_invite(
      services,
      email,
      organization,
      normal_user,
      membership_type=MembershipType.owner,
    )
    assert len(services.invite_service.find_by_email(email, valid_only=False)) == 1
    assert len(services.invite_service.find_by_email(email, valid_only=True)) == 1
    services.membership_service.delete(membership)
    assert len(services.invite_service.find_by_email(email, valid_only=False)) == 1
    assert len(services.invite_service.find_by_email(email, valid_only=True)) == 0
