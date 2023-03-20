# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.service.test_base import ServiceBase


class TestMembershipCreate(ServiceBase):
  def test_create_if_not_exists(self, services, normal_user):
    organization = self.make_organization(services, "Test Organization 1")
    membership = services.membership_service.find_by_user_and_organization(
      user_id=normal_user.id, organization_id=organization.id
    )
    assert membership is None
    services.membership_service.create_if_not_exists(user_id=normal_user.id, organization_id=organization.id)
    membership = services.membership_service.find_by_user_and_organization(
      user_id=normal_user.id, organization_id=organization.id
    )
    assert membership is not None
    assert membership.user_id == normal_user.id
    assert membership.organization_id == organization.id
    services.membership_service.create_if_not_exists(user_id=normal_user.id, organization_id=organization.id)
    num_memberships_in_organization = services.membership_service.count_by_organization_id(organization.id)
    assert num_memberships_in_organization == 1
