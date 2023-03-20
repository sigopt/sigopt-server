# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.lists import find
from zigopt.invite.constant import NO_ROLE, READ_ONLY_ROLE, USER_ROLE

from integration.v1.endpoints.invites.test_base import InviteTestBase


class TestUserPermissionsList(InviteTestBase):
  def test_list_user_permissions(self, services, owner_connection, invitee, invitee_connection, inbox, config_broker):
    client_1 = owner_connection.clients().create(name="Test Client 1")
    client_2 = owner_connection.clients().create(name="Test Client 2")

    owner_connection.clients(client_1.id).invites().create(email=invitee.email, role=USER_ROLE, old_role=NO_ROLE)
    owner_connection.clients(client_2.id).invites().create(email=invitee.email, role=READ_ONLY_ROLE, old_role=NO_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)

    permissions = invitee_connection.users(invitee_connection.user_id).permissions().fetch()
    assert len(permissions.data) == 3

    client_1_permission = find(permissions.data, lambda p: p.client.id == client_1.id)
    assert client_1_permission.can_write
    assert not client_1_permission.can_admin
    client_2_permission = find(permissions.data, lambda p: p.client.id == client_2.id)
    assert client_2_permission.can_read
    assert not client_2_permission.can_write

  def test_list_user_permissions_in_org(
    self, services, owner_connection, invitee, invitee_connection, inbox, config_broker
  ):
    client_1 = owner_connection.clients().create(name="Test Client 1")
    client_2 = owner_connection.clients().create(name="Test Client 2")

    owner_connection.clients(client_1.id).invites().create(email=invitee.email, role=USER_ROLE, old_role=NO_ROLE)
    owner_connection.clients(client_2.id).invites().create(email=invitee.email, role=READ_ONLY_ROLE, old_role=NO_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)

    permissions = (
      invitee_connection.users(invitee_connection.user_id).permissions().fetch(organization=client_1.organization)
    )
    assert len(permissions.data) == 1

    client_1_permission = permissions.data[0]
    assert client_1_permission.can_write
    assert not client_1_permission.can_admin

    client_3 = owner_connection.organizations(client_1.organization).clients().create(name="Another Client")
    owner_connection.clients(client_3.id).invites().create(email=invitee.email, role=USER_ROLE, old_role=NO_ROLE)

    permissions = (
      invitee_connection.users(invitee_connection.user_id).permissions().fetch(organization=client_1.organization)
    )
    assert len(permissions.data) == 2
