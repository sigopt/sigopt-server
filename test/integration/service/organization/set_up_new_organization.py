# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.user.model import User

from integration.service.test_base import ServiceBase
from integration.utils.random_email import generate_random_email


class TestOrganizationServiceSetUpNewOrganization(ServiceBase):
  @pytest.mark.parametrize("allow_users_to_see_experiments_by_others", [True, False])
  @pytest.mark.parametrize("academic", [True, False])
  @pytest.mark.parametrize("user_is_owner", [True, False])
  def test_set_up_new_organization(self, services, academic, allow_users_to_see_experiments_by_others, user_is_owner):
    user = User(name="new organization user", email=generate_random_email())
    services.user_service.insert(user)

    (organization, _) = services.organization_service.set_up_new_organization(
      "some organization name",
      "some client name",
      user,
      allow_users_to_see_experiments_by_others=allow_users_to_see_experiments_by_others,
      academic=academic,
      user_is_owner=user_is_owner,
      requestor=user,
    )
    assert organization.id is not None
    assert organization.name == "some organization name"
    assert organization.academic is academic
    assert user_is_owner == services.membership_service.user_is_owner_for_organization(user.id, organization.id)
