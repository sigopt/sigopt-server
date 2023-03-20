# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.authorization.constant import AuthorizationDenied
from zigopt.authorization.user import UserAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE

from sigopttest.authorization.test_base import _TestAuthorizationCore


class TestUserAuthorization(_TestAuthorizationCore):
  @pytest.mark.parametrize(
    "scoped_membership,scoped_permission",
    (
      (None, None),
      (_TestAuthorizationCore.membership, None),
    ),
  )
  def test_user(self, services, scoped_membership, scoped_permission):
    user_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=False,
      user_id=self.user_id,
    )

    auth = UserAuthorization(
      current_user=Mock(
        id=self.user_id,
      ),
      user_token=user_token,
      scoped_membership=scoped_membership,
      scoped_permission=scoped_permission,
    )

    assert auth.current_client is None
    assert auth.current_user.id == self.user_id
    assert auth.api_token == user_token
    assert auth.can_act_on_user(services, READ, self.user)
    assert auth.can_act_on_user(services, WRITE, self.user)
    assert auth.can_act_on_user(services, ADMIN, self.user)
    assert auth.can_act_on_user(services, READ, self.user_in_same_organization)
    assert not auth.can_act_on_user(services, WRITE, self.user_in_same_organization)
    assert not auth.can_act_on_user(services, ADMIN, self.user_in_same_organization)
    assert auth.can_act_on_user(services, READ, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, WRITE, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, ADMIN, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert not auth.can_act_on_user(services, READ, self.user_with_no_role)
    assert not auth.can_act_on_user(services, WRITE, self.user_with_no_role)
    assert not auth.can_act_on_user(services, ADMIN, self.user_with_no_role)

    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert auth.can_act_on_client(services, ADMIN, self.client)
    assert auth.can_act_on_client(services, READ, self.client_in_same_organization)
    assert auth.can_act_on_client(services, WRITE, self.client_in_same_organization)
    assert auth.can_act_on_client(services, ADMIN, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)

    assert auth.can_act_on_organization(services, READ, self.organization)
    assert auth.can_act_on_organization(services, WRITE, self.organization)
    assert auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)

    assert auth.can_act_on_experiment(services, READ, self.experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)

    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)

  @pytest.mark.parametrize(
    "scoped_membership,scoped_permission",
    (
      (None, None),
      (_TestAuthorizationCore.non_owner_user_membership, None),
      (_TestAuthorizationCore.non_owner_user_membership, _TestAuthorizationCore.current_client_non_owner_user_role),
    ),
  )
  def test_non_owner_user(self, services, scoped_membership, scoped_permission):
    non_owner_user_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=False,
      user_id=self.non_owner_user_id,
    )

    auth = UserAuthorization(
      current_user=Mock(
        id=self.non_owner_user_id,
      ),
      user_token=non_owner_user_token,
      scoped_membership=scoped_membership,
      scoped_permission=scoped_permission,
    )

    assert auth.current_client is None
    assert auth.current_user.id == self.non_owner_user_id
    assert auth.api_token == non_owner_user_token

    assert auth.can_act_on_user(services, READ, self.non_owner_user)
    assert auth.can_act_on_user(services, WRITE, self.non_owner_user)
    assert auth.can_act_on_user(services, ADMIN, self.non_owner_user)
    assert not auth.can_act_on_user(services, READ, self.user_in_same_organization)
    assert not auth.can_act_on_user(services, WRITE, self.user_in_same_organization)
    assert not auth.can_act_on_user(services, ADMIN, self.user_in_same_organization)
    assert auth.can_act_on_user(services, READ, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, WRITE, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, ADMIN, self.user_with_same_client_for_role)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert not auth.can_act_on_user(services, READ, self.user_with_no_role)
    assert not auth.can_act_on_user(services, WRITE, self.user_with_no_role)
    assert not auth.can_act_on_user(services, ADMIN, self.user_with_no_role)

    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, WRITE, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, ADMIN, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)

    assert auth.can_act_on_organization(services, READ, self.organization)
    assert not auth.can_act_on_organization(services, WRITE, self.organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)

    assert auth.can_act_on_experiment(services, READ, self.experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)

    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)

  def test_user_private_experiments(self, services):
    user_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=False,
      user_id=self.user_id,
    )

    auth = UserAuthorization(
      current_user=Mock(
        id=self.user_id,
      ),
      user_token=user_token,
      scoped_membership=None,
      scoped_permission=None,
    )
    assert auth.can_act_on_experiment(services, READ, self.experiment_private_client)
    assert auth.can_act_on_experiment(services, WRITE, self.experiment_private_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_private_client)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment_private_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment_private_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment_private_client)

    assert auth.can_act_on_project(services, READ, self.project_private_client)
    assert auth.can_act_on_project(services, WRITE, self.project_private_client)
    assert not auth.can_act_on_project(services, ADMIN, self.project_private_client)
    assert not auth.can_act_on_project(services, READ, self.other_project_private_client)
    assert not auth.can_act_on_project(services, WRITE, self.other_project_private_client)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project_private_client)

  def test_needs_email_verification(self, services):
    user_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=False,
      user_id=self.user_id,
    )
    current_user = Mock(
      id=self.user_id,
    )
    auth = UserAuthorization(
      current_user=current_user,
      user_token=user_token,
      scoped_membership=None,
      scoped_permission=None,
    )

    services.invite_service.can_have_membership_to_organization.return_value = True
    services.email_verification_service.has_verified_email_if_needed.return_value = True
    assert auth.can_act_on_organization(services, READ, self.organization) is True

    services.invite_service.can_have_membership_to_organization.return_value = False
    services.email_verification_service.has_verified_email_if_needed.return_value = True
    assert auth.can_act_on_organization(services, READ, self.organization) is False

    services.invite_service.can_have_membership_to_organization.return_value = False
    services.email_verification_service.has_verified_email_if_needed.return_value = False
    assert (
      auth.can_act_on_organization(services, READ, self.organization) is AuthorizationDenied.NEEDS_EMAIL_VERIFICATION
    )
