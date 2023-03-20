# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.invite.constant import ADMIN_ROLE, USER_ROLE
from zigopt.membership.model import MembershipType

from integration.service.test_base import ServiceBase


class TestOrganizationMerge(ServiceBase):
  @pytest.mark.slow
  def test_merge_organizations(self, services, config_broker):
    if not config_broker.get("features.allowCreateOrganization"):
      pytest.skip()
    dest_org = self.make_organization(services, "Destination Organization")
    org1 = self.make_organization(services, "Test Merge Organization 1")
    org2 = self.make_organization(services, "Test Merge Organization 2")

    org1_client1 = self.make_client(services, "Organization 1 Client 1", org1)
    org1_client2 = self.make_client(services, "Organization 1 Client 2", org1)
    org2_client3 = self.make_client(services, "Organization 2 Client 1", org2)

    alice = self.make_user(services, "alice")
    bob = self.make_user(services, "bob")
    charles_email = "charles@sigopt.ninja"
    dave_email = "dave@sigopt.ninja"
    ed = self.make_user(services, "ed")

    self.make_membership(services, alice, org1, is_owner=True)
    self.make_membership(services, alice, org2)
    self.make_membership(services, bob, org1)
    self.make_membership(services, ed, dest_org, is_owner=True)
    self.make_membership(services, ed, org1)

    self.make_permission(services, bob, org1_client1, ADMIN_ROLE)
    self.make_permission(services, bob, org1_client2, ADMIN_ROLE)
    self.make_permission(services, alice, org2_client3, ADMIN_ROLE)
    self.make_permission(services, ed, org1_client1, ADMIN_ROLE)

    charles_org1_invite = self.make_invite(services, charles_email, org1, alice, MembershipType.member)
    self.make_pending_permission(
      services,
      charles_org1_invite,
      org1_client1,
      USER_ROLE,
    )
    self.make_pending_permission(
      services,
      charles_org1_invite,
      org1_client2,
      USER_ROLE,
    )

    self.make_invite(services, charles_email, org2, alice, MembershipType.owner)

    dave_org2_invite = self.make_invite(services, dave_email, org2, alice, MembershipType.member)
    self.make_pending_permission(
      services,
      dave_org2_invite,
      org2_client3,
      USER_ROLE,
    )

    # Confirm that dest_org is empty and org1 and org2 have clients, permissions, invites, etc.
    num_clients_in_dest_org = services.client_service.count_by_organization_id(dest_org.id)
    assert num_clients_in_dest_org == 0
    num_clients_in_org1 = services.client_service.count_by_organization_id(org1.id)
    assert num_clients_in_org1 == 2
    num_clients_in_org2 = services.client_service.count_by_organization_id(org2.id)
    assert num_clients_in_org2 == 1

    num_memberships_in_dest_org = services.membership_service.count_by_organization_id(dest_org.id)
    assert num_memberships_in_dest_org == 1
    num_memberships_in_org1 = services.membership_service.count_by_organization_id(org1.id)
    assert num_memberships_in_org1 == 3
    num_memberships_in_org2 = services.membership_service.count_by_organization_id(org2.id)
    assert num_memberships_in_org2 == 1

    num_permissions_in_dest_org = services.permission_service.count_by_organization_id(dest_org.id)
    assert num_permissions_in_dest_org == 0
    num_permissions_in_org1 = services.permission_service.count_by_organization_id(org1.id)
    assert num_permissions_in_org1 == 3
    num_permissions_in_org2 = services.permission_service.count_by_organization_id(org2.id)
    assert num_permissions_in_org2 == 1

    invites_to_dest_org = services.invite_service.find_by_organization_id(dest_org.id)
    assert len(invites_to_dest_org) == 0
    invites_to_org1 = services.invite_service.find_by_organization_id(org1.id)
    assert len(invites_to_org1) == 1
    invites_to_org2 = services.invite_service.find_by_organization_id(org2.id)
    assert len(invites_to_org2) == 2

    pending_permissions_dest_org = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_dest_org]
    )
    assert len(pending_permissions_dest_org) == 0
    pending_permissions_org1 = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_org1]
    )
    assert len(pending_permissions_org1) == 2
    pending_permissions_org2 = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_org2]
    )
    assert len(pending_permissions_org2) == 1

    # Merge org1 and org2 into dest_org
    orgs_to_merge = [org1.id, org2.id]
    services.organization_service.merge_organizations_into_destination(
      dest_org.id,
      orgs_to_merge,
      requestor=alice,
    )

    # Confirm that dest_org now contains all the data of org1 and org2
    num_clients_in_dest_org = services.client_service.count_by_organization_id(dest_org.id)
    assert num_clients_in_dest_org == 3
    num_clients_in_org1 = services.client_service.count_by_organization_id(org1.id)
    assert num_clients_in_org1 == 0
    num_clients_in_org2 = services.client_service.count_by_organization_id(org2.id)
    assert num_clients_in_org2 == 0

    num_memberships_in_dest_org = services.membership_service.count_by_organization_id(dest_org.id)
    assert num_memberships_in_dest_org == 3
    num_memberships_in_org1 = services.membership_service.count_by_organization_id(org1.id)
    assert num_memberships_in_org1 == 0
    num_memberships_in_org2 = services.membership_service.count_by_organization_id(org2.id)
    assert num_memberships_in_org2 == 0

    num_permissions_in_dest_org = services.permission_service.count_by_organization_id(dest_org.id)
    assert num_permissions_in_dest_org == 5
    num_permissions_in_org1 = services.permission_service.count_by_organization_id(org1.id)
    assert num_permissions_in_org1 == 0
    num_permissions_in_org2 = services.permission_service.count_by_organization_id(org2.id)
    assert num_permissions_in_org2 == 0

    invites_to_dest_org = services.invite_service.find_by_organization_id(dest_org.id)
    assert len(invites_to_dest_org) == 2
    invites_to_org1 = services.invite_service.find_by_organization_id(org1.id)
    assert len(invites_to_org1) == 0
    invites_to_org2 = services.invite_service.find_by_organization_id(org2.id)
    assert len(invites_to_org2) == 0

    pending_permissions_dest_org = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_dest_org]
    )
    assert len(pending_permissions_dest_org) == 3
    pending_permissions_org1 = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_org1]
    )
    assert len(pending_permissions_org1) == 0
    pending_permissions_org2 = services.pending_permission_service.find_by_invite_ids(
      [invite.id for invite in invites_to_org2]
    )
    assert len(pending_permissions_org2) == 0
