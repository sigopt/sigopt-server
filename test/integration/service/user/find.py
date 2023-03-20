# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.membership.model import MembershipType

from integration.service.test_base import ServiceBase


class TestUserFind(ServiceBase):
  def test_find_owned_clients(self, services, organization, other_organization, client, other_client):
    user = self.make_user(services, "Random User")
    services.membership_service.create_if_not_exists(
      user_id=user.id,
      organization_id=organization.id,
      membership_type=MembershipType.owner,
    )
    services.membership_service.create_if_not_exists(
      user_id=user.id,
      organization_id=other_organization.id,
      membership_type=MembershipType.member,
    )
    owned_clients = services.user_service.find_owned_clients(user)
    assert len(owned_clients) == 1
    assert owned_clients[0].id == client.id

    self.make_client(services, "Another Client to Own", organization)

    owned_clients = services.user_service.find_owned_clients(user)
    assert len(owned_clients) == 2
