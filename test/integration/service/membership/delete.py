# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.invite.constant import ADMIN_ROLE

from integration.service.test_base import ServiceBase


class TestMembershipDelete(ServiceBase):
  def test_delete_by_organization_id(self, services, normal_user):
    organization1 = self.make_organization(services, "Test Organization 1")
    organization2 = self.make_organization(services, "Test Organization 2")
    self.make_membership(services, normal_user, organization1)
    self.make_membership(services, normal_user, organization2)
    num_membership_organization_1 = services.membership_service.count_by_organization_id(organization1.id)
    num_membership_organization_2 = services.membership_service.count_by_organization_id(organization2.id)
    assert num_membership_organization_1 == 1
    assert num_membership_organization_2 == 1
    services.membership_service.delete_by_organization_id(organization1.id)
    num_membership_organization_1 = services.membership_service.count_by_organization_id(organization1.id)
    num_membership_organization_2 = services.membership_service.count_by_organization_id(organization2.id)
    assert num_membership_organization_1 == 0
    assert num_membership_organization_2 == 1

  def test_delete_by_organization_and_user(self, services, normal_user):
    second_user = self.make_user(services, "Second User")
    organization1 = self.make_organization(services, "Test Organization 1")
    organization2 = self.make_organization(services, "Test Organization 2")
    self.make_membership(services, normal_user, organization1)
    self.make_membership(services, normal_user, organization2)
    self.make_membership(services, second_user, organization1)
    self.make_membership(services, second_user, organization2)
    num_membership_org_1 = services.membership_service.count_by_organization_id(organization1.id)
    num_membership_org_2 = services.membership_service.count_by_organization_id(organization2.id)
    assert num_membership_org_1 == 2
    assert num_membership_org_2 == 2
    services.membership_service.delete_by_organization_and_user(organization1.id, normal_user.id)
    num_membership_org_1 = services.membership_service.count_by_organization_id(organization1.id)
    assert num_membership_org_1 == 1
    deleted_membership = services.membership_service.find_by_user_and_organization(normal_user.id, organization1.id)
    assert not deleted_membership

  def test_delete_by_user_id(self, services, normal_user):
    second_user = self.make_user(services, "Second User")
    organization = self.make_organization(services, "Test Organization 1")
    self.make_membership(services, normal_user, organization)
    self.make_membership(services, second_user, organization)
    num_membership = services.membership_service.count_by_organization_id(organization.id)
    assert num_membership == 2
    services.membership_service.delete_by_organization_and_user(organization.id, normal_user.id)
    existing_membership = services.membership_service.find_by_user_and_organization(second_user.id, organization.id)
    assert existing_membership
    no_membership = services.membership_service.find_by_user_and_organization(normal_user.id, organization.id)
    assert no_membership is None

  def test_delete_stray_memberships_by_organization(self, services, normal_user, organization, client):
    second_user = self.make_user(services, "Second User")
    self.make_membership(services, normal_user, organization)
    self.make_permission(services, normal_user, client, ADMIN_ROLE)
    self.make_membership(services, second_user, organization, is_owner=True)

    assert services.membership_service.count_by_organization_id(organization.id) == 2
    services.membership_service.delete_stray_memberships_by_organization(organization.id)
    assert services.membership_service.count_by_organization_id(organization.id) == 2

    services.permission_service.delete_by_client_and_user(client.id, normal_user.id)
    assert services.membership_service.count_by_organization_id(organization.id) == 2
    services.membership_service.delete_stray_memberships_by_organization(organization.id)
    assert services.membership_service.count_by_organization_id(organization.id) == 1
