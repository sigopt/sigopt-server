# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.invite.constant import USER_ROLE

from integration.service.test_base import ServiceBase
from integration.utils.random_email import generate_random_email


class TestInviteDelete(ServiceBase):
  @pytest.fixture(scope="function")
  def email(self):
    return generate_random_email()

  @pytest.fixture(scope="function")
  def other_email(self):
    return generate_random_email()

  def test_delete_by_email(self, services, normal_user, email, other_email):
    organization = self.make_organization(services, "Test Organization")
    services.membership_service.insert(normal_user.id, organization.id)
    self.make_client(services, "Test Client 1", organization)

    self.make_invite(services, email, organization, normal_user)
    self.make_invite(services, other_email, organization, normal_user)

    invites_to_client1 = services.invite_service.find_by_organization_id(organization.id)
    assert len(invites_to_client1) == 2

    services.invite_service.delete_by_email(email)

    invites_to_email = services.invite_service.find_by_email(email, valid_only=False)
    assert len(invites_to_email) == 0
    invites_to_email = services.invite_service.find_by_email(other_email, valid_only=False)
    assert len(invites_to_email) == 1

  def test_delete_by_email_and_organization(self, services, normal_user, email):
    organization1 = self.make_organization(services, "Test Organization 1")
    organization2 = self.make_organization(services, "Test Organization 2")

    services.membership_service.insert(normal_user.id, organization1.id)
    services.membership_service.insert(normal_user.id, organization2.id)

    self.make_client(services, "Organization 1 Client", organization1)
    self.make_client(services, "Organization 2 Client", organization2)

    self.make_invite(services, email, organization1, normal_user)
    self.make_invite(services, email, organization2, normal_user)

    invites_to_org1 = services.invite_service.find_by_organization_id(organization1.id)
    assert len(invites_to_org1) == 1
    invites_to_org2 = services.invite_service.find_by_organization_id(organization2.id)
    assert len(invites_to_org2) == 1

    services.invite_service.delete_by_email_and_organization(email, organization1.id)

    invites_to_org1 = services.invite_service.find_by_organization_id(organization1.id)
    assert len(invites_to_org1) == 0
    invites_to_org2 = services.invite_service.find_by_organization_id(organization2.id)
    assert len(invites_to_org2) == 1

  def test_delete_stray_invites_by_organization(self, services, normal_user, email, other_email):
    # pylint: disable=too-many-locals
    claimable_email = email
    stray_email = other_email

    second_user = self.make_user(services, "Second User")
    organization = self.make_organization(services, "Test Organization")
    services.membership_service.insert(normal_user.id, organization.id)
    services.membership_service.insert(second_user.id, organization.id)
    client = self.make_client(services, "Test Client", organization)
    invite1 = self.make_invite(services, claimable_email, organization, normal_user)
    invite2 = self.make_invite(services, stray_email, organization, second_user)

    pending_permission1 = services.pending_permission_service.create_pending_permission(invite1, client, USER_ROLE)
    services.pending_permission_service.insert(pending_permission1)

    num_pending_permissions_invite1 = services.pending_permission_service.count_by_invite_id(invite1.id)
    assert num_pending_permissions_invite1 == 1
    num_pending_permissions_invite2 = services.pending_permission_service.count_by_invite_id(invite2.id)
    assert num_pending_permissions_invite2 == 0

    services.invite_service.delete_stray_invites_by_organization(organization.id)

    nonstrayinvite = services.invite_service.find_by_email_and_organization(claimable_email, organization.id)
    assert nonstrayinvite.id == invite1.id
    strayinvite = services.invite_service.find_by_email_and_organization(stray_email, organization.id)
    assert strayinvite is None

  def test_delete_stray_invites_deletes_from_correct_organization(self, services, normal_user, email, other_email):
    organization1 = self.make_organization(services, "Test Organization 1")
    organization2 = self.make_organization(services, "Test Organization 2")
    services.membership_service.insert(normal_user.id, organization1.id)
    services.membership_service.insert(normal_user.id, organization2.id)
    self.make_client(services, "Test Client 1", organization1)
    self.make_client(services, "Test Client 2", organization1)

    stray_email_1 = email
    stray_email_2 = other_email

    invite1 = self.make_invite(services, stray_email_1, organization1, normal_user)
    self.make_invite(services, stray_email_2, organization2, normal_user)

    services.invite_service.delete_stray_invites_by_organization(organization2.id)

    existing_stray_invite = services.invite_service.find_by_email_and_organization(stray_email_1, organization1.id)
    assert existing_stray_invite.id == invite1.id
    deleted_stray_invite = services.invite_service.find_by_email_and_organization(stray_email_2, organization2.id)
    assert deleted_stray_invite is None
