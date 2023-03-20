# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.permission.pending.model import PendingPermission

from integration.service.test_base import ServiceBase


class TestPendingPermissionDelete(ServiceBase):
  def test_find_by_invite_id(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    client = self.make_client(services, "Test Client", organization)
    services.membership_service.insert(normal_user.id, organization.id)
    invite1 = self.make_invite(
      services=services,
      email="inviteduser1@sigopt.ninja",
      organization=organization,
      inviter=normal_user,
    )
    invite2 = self.make_invite(
      services=services,
      email="inviteduser2@sigopt.ninja",
      organization=organization,
      inviter=normal_user,
    )
    pending_permission1 = PendingPermission(invite_id=invite1.id, client_id=client.id, organization_id=organization.id)
    pending_permission1 = services.pending_permission_service.insert(pending_permission1)
    pending_permission2 = PendingPermission(invite_id=invite2.id, client_id=client.id, organization_id=organization.id)
    pending_permission2 = services.pending_permission_service.insert(pending_permission2)

    pending_permissions_of_invite1 = services.pending_permission_service.find_by_invite_id(invite1.id)
    assert len(pending_permissions_of_invite1) == 1
    assert pending_permissions_of_invite1[0].id == pending_permission1.id

    pending_permissions_of_invite2 = services.pending_permission_service.find_by_invite_id(invite2.id)
    assert len(pending_permissions_of_invite2) == 1
    assert pending_permissions_of_invite2[0].id == pending_permission2.id

  def test_find_by_client_id(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization")
    client1 = self.make_client(services, "Test Client 1", organization)
    client2 = self.make_client(services, "Test Client 2", organization)
    services.membership_service.insert(normal_user.id, organization.id)
    invite = self.make_invite(
      services=services,
      email="inviteduser1@sigopt.ninja",
      organization=organization,
      inviter=normal_user,
    )
    pending_permission1 = PendingPermission(invite_id=invite.id, client_id=client1.id, organization_id=organization.id)
    pending_permission1 = services.pending_permission_service.insert(pending_permission1)
    pending_permission2 = PendingPermission(invite_id=invite.id, client_id=client2.id, organization_id=organization.id)
    pending_permission2 = services.pending_permission_service.insert(pending_permission2)

    pending_permissions_of_client1 = services.pending_permission_service.find_by_client_id(client1.id)
    assert len(pending_permissions_of_client1) == 1
    assert pending_permissions_of_client1[0].id == pending_permission1.id

    pending_permissions_of_client2 = services.pending_permission_service.find_by_client_id(client2.id)
    assert len(pending_permissions_of_client2) == 1
    assert pending_permissions_of_client2[0].id == pending_permission2.id
