# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.membership.model import MembershipType

from integration.service.test_base import ServiceBase


class TestMembershipLogic(ServiceBase):
  def test_find_owners(self, services, normal_user, organization, client, other_organization, other_client):
    assert services.membership_service.find_owners_by_user_id(normal_user.id) == []
    assert services.membership_service.find_owners_by_organization_id(organization.id) == []
    assert services.membership_service.find_owners_by_organization_id(other_organization.id) == []
    self.make_membership(services, normal_user, organization, is_owner=True)
    self.make_membership(services, normal_user, other_organization, is_owner=False)
    owner_memberships = services.membership_service.find_owners_by_user_id(normal_user.id)
    assert len(owner_memberships) == 1
    for membership in owner_memberships:
      assert membership.user_id == normal_user.id
      assert membership.organization_id == organization.id
      assert membership.is_owner
    owner_memberships = services.membership_service.find_owners_by_organization_id(organization.id)
    assert len(owner_memberships) == 1
    for membership in owner_memberships:
      assert membership.user_id == normal_user.id
      assert membership.organization_id == organization.id
      assert membership.is_owner
    owner_memberships = services.membership_service.find_owners_by_organization_id(client.organization_id)
    for membership in owner_memberships:
      assert membership.user_id == normal_user.id
      assert membership.organization_id == client.organization_id
      assert membership.is_owner
    assert services.membership_service.find_owners_by_organization_id(other_organization.id) == []
    assert services.membership_service.find_owners_by_organization_id(other_client.organization_id) == []

  def test_user_is_owner(self, services, normal_user, organization, client, other_organization, other_client):
    assert not services.membership_service.user_is_owner_for_organization(
      user_id=normal_user.id,
      organization_id=organization.id,
    )
    assert not services.membership_service.user_is_owner_for_organization(
      user_id=normal_user.id,
      organization_id=organization.id,
    )
    self.make_membership(services, normal_user, organization, is_owner=True)
    self.make_membership(services, normal_user, other_organization, is_owner=False)
    assert services.membership_service.user_is_owner_for_organization(
      user_id=normal_user.id,
      organization_id=organization.id,
    )
    assert not services.membership_service.user_is_owner_for_organization(
      user_id=normal_user.id,
      organization_id=other_organization.id,
    )

  def _assert_users_mutually_visible(self, services, user1, user2):
    assert services.membership_service.users_are_mutually_visible(user1_id=user1.id, user2_id=user2.id)
    assert services.membership_service.users_are_mutually_visible(user1_id=user2.id, user2_id=user1.id)

  def _assert_users_not_mutually_visible(self, services, user1, user2):
    assert not services.membership_service.users_are_mutually_visible(user1_id=user1.id, user2_id=user2.id)
    assert not services.membership_service.users_are_mutually_visible(user1_id=user2.id, user2_id=user1.id)

  def test_users_are_mutually_visible(self, services, normal_user):
    organization1 = self.make_organization(services, "Test Organization 1")
    organization2 = self.make_organization(services, "Test Organization 2")
    organization3 = self.make_organization(services, "Test Organization 3")
    alice = normal_user
    bob = self.make_user(services, "Bob")
    charlie = self.make_user(services, "Charlie")
    alice_membership1 = self.make_membership(services, alice, organization1)
    self.make_membership(services, bob, organization2)
    self.make_membership(services, charlie, organization3)

    # no users share an organization
    for user1 in (alice, bob, charlie):
      for user2 in (alice, bob, charlie):
        if user1 is user2:
          continue
        self._assert_users_not_mutually_visible(services, user1, user2)

    self.make_membership(services, alice, organization2)
    bob_membership1 = self.make_membership(services, bob, organization1)

    # bob and alice are members in the same organization but neither are owners
    self._assert_users_not_mutually_visible(services, alice, bob)

    # charlie still can't see bob or alice
    self._assert_users_not_mutually_visible(services, alice, charlie)
    self._assert_users_not_mutually_visible(services, bob, charlie)

    services.membership_service.elevate_to_owner(alice_membership1)

    # alice is an owner of organization1 so alice and bob can see each other
    self._assert_users_mutually_visible(services, alice, bob)

    # charlie still can't see bob or alice
    self._assert_users_not_mutually_visible(services, alice, charlie)
    self._assert_users_not_mutually_visible(services, bob, charlie)

    services.membership_service.elevate_to_owner(bob_membership1)

    # alice and bob are owners of organization1 so they can see each other
    self._assert_users_mutually_visible(services, alice, bob)

    # charlie still can't see bob or alice
    self._assert_users_not_mutually_visible(services, alice, charlie)
    self._assert_users_not_mutually_visible(services, bob, charlie)

  def test_elevate_to_owner(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    m = self.make_membership(services, normal_user, organization, is_owner=False)
    assert m.membership_type == MembershipType.member

    services.membership_service.elevate_to_owner(m)

    assert m.membership_type == MembershipType.owner
