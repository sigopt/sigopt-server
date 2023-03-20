# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.test_base import V1Base


class TestUserMembershipsList(V1Base):
  def test_list(self, connection, owner_connection_same_organization, services):
    memberships = connection.users(connection.user_id).memberships().fetch().data
    num_organizations = len(services.membership_service.find_by_user_id(connection.user_id))
    assert len(memberships) == num_organizations

    user = services.user_service.find_by_id(owner_connection_same_organization.user_id)
    organization_name = "Test Organization"
    (organization, _) = services.organization_service.set_up_new_organization(
      organization_name=organization_name,
      client_name=organization_name,
      user=user,
      allow_users_to_see_experiments_by_others=True,
      requestor=user,
      user_is_owner=True,
    )

    memberships = connection.users(connection.user_id).memberships().fetch().data
    assert len(memberships) == num_organizations

    owner_connection_same_organization.organizations(organization.id).invites().create(
      email=connection.email, membership_type="owner"
    )
    memberships = connection.users(connection.user_id).memberships().fetch().data
    assert len(memberships) == num_organizations + 1

  def test_list_for_organization(self, owner_connection_same_organization, owner_connection, connection, services):
    user = services.user_service.find_by_id(owner_connection_same_organization.user_id)
    organization_name = "Test Organization"
    (organization, _) = services.organization_service.set_up_new_organization(
      organization_name=organization_name,
      client_name=organization_name,
      user=user,
      allow_users_to_see_experiments_by_others=True,
      requestor=user,
      user_is_owner=True,
    )

    owner_connection_same_organization.organizations(organization.id).invites().create(
      email=connection.email, membership_type="owner"
    )

    memberships = connection.users(connection.user_id).memberships().fetch().data
    num_organizations = len(services.membership_service.find_by_user_id(connection.user_id))
    assert len(memberships) == num_organizations

    memberships_for_organization = (
      connection.users(connection.user_id).memberships().fetch(organization=organization.id).data
    )
    assert len(memberships_for_organization) == 1

    no_memberships = (
      owner_connection.users(owner_connection.user_id).memberships().fetch(organization=organization.id).data
    )
    assert len(no_memberships) == 0
