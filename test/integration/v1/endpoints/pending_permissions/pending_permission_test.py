# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.invite.constant import NO_ROLE, USER_ROLE

from integration.utils.random_email import generate_random_email
from integration.v1.test_base import V1Base


class TestPendingPermissionList(V1Base):
  def test_pending_permissions_list(self, services, connection):
    client = connection.clients(connection.client_id).fetch()

    pending_permissions = connection.clients(client.id).pending_permissions().fetch().data
    assert len(pending_permissions) == 0

    email = generate_random_email()
    connection.clients(client.id).invites().create(email=email, role=USER_ROLE, old_role=NO_ROLE)
    pending_permissions = connection.clients(client.id).pending_permissions().fetch().data
    assert len(pending_permissions) == 1
    assert pending_permissions[0].role == USER_ROLE
    assert pending_permissions[0].email == email.lower()
    assert pending_permissions[0].client_name == client.name
    assert pending_permissions[0].client == client.id
