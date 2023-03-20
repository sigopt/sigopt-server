# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.authorization.member import OrganizationMemberAuthorization
from zigopt.authorization.owner import OrganizationOwnerAuthorization
from zigopt.authorization.user import UserAuthorization
from zigopt.membership.model import Membership, MembershipType
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE

from sigopttest.authorization.test_base import _TestAuthorizationCore


class BaseTestClientUserAuthorization(_TestAuthorizationCore):
  @pytest.fixture
  def client_token(self):
    return Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=False,
      client_id=self.client_id,
    )


class TestOrganizationMemberAuthorization(BaseTestClientUserAuthorization):
  def test_role(self, services, client_token):
    current_user = Mock(id=self.non_owner_user_id)
    current_membership = Mock(
      spec=Membership,
      user_id=self.non_owner_user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.member,
      is_owner=False,
    )
    current_permission = Mock(
      spec=Permission,
      id=self.permission_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      user_id=self.non_owner_user_id,
      can_read=True,
      can_write=True,
      can_admin=False,
      can_see_experiments_by_others=True,
    )
    auth = OrganizationMemberAuthorization(
      current_client=Mock(id=self.client_id),
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=current_permission,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.non_owner_user_id
    assert auth.api_token == client_token
    assert auth.can_act_on_user(services, READ, self.non_owner_user)
    assert auth.can_act_on_user(services, WRITE, self.non_owner_user)
    assert auth.can_act_on_user(services, ADMIN, self.non_owner_user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
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
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)

  def test_non_owner(self, services, client_token):
    current_user = Mock(id=self.non_owner_user_id)
    current_membership = Mock(
      spec=Membership,
      user_id=self.non_owner_user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.member,
      is_owner=False,
    )
    current_permission = Mock(
      spec=Permission,
      id=self.permission_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      user_id=self.non_owner_user_id,
      can_read=True,
      can_write=True,
      can_admin=False,
      can_see_experiments_by_others=True,
    )
    auth = OrganizationMemberAuthorization(
      current_client=Mock(id=self.client_id),
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=current_permission,
      ),
    )
    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.non_owner_user_id
    assert auth.api_token == client_token
    assert auth.can_act_on_user(services, READ, self.non_owner_user)
    assert auth.can_act_on_user(services, WRITE, self.non_owner_user)
    assert auth.can_act_on_user(services, ADMIN, self.non_owner_user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
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
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)

  def test_role_read(self, services):
    current_user = Mock(id=self.non_owner_user_id)
    current_membership = Mock(
      spec=Membership,
      user_id=self.non_owner_user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.member,
      is_owner=False,
    )
    current_permission = Mock(
      spec=Permission,
      id=self.permission_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      user_id=self.non_owner_user_id,
      can_read=True,
      can_write=False,
      can_admin=False,
      can_see_experiments_by_others=True,
    )
    auth = OrganizationMemberAuthorization(
      current_client=Mock(id=self.client_id),
      current_user=current_user,
      client_token=Mock(
        all_experiments=True,
        guest_experiment_id=None,
        development=False,
        client_id=self.client_id,
      ),
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=current_permission,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.non_owner_user_id
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert auth.can_act_on_user(services, READ, self.non_owner_user)
    assert auth.can_act_on_user(services, WRITE, self.non_owner_user)
    assert auth.can_act_on_user(services, ADMIN, self.non_owner_user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert not auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, WRITE, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, ADMIN, self.client_in_same_organization)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)
    assert auth.can_act_on_experiment(services, READ, self.experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert not auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert not auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)

  def test_role_development(self, services):
    current_user = Mock(id=self.user_id)
    client_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=True,
      client_id=self.client_id,
    )

    current_membership = Mock(
      spec=Membership,
      user_id=self.user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.member,
      is_owner=False,
    )

    current_permission = Mock(
      spec=Permission,
      id=self.permission_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      user_id=self.user_id,
      can_read=True,
      can_write=True,
      can_admin=False,
      can_see_experiments_by_others=True,
    )

    auth = OrganizationMemberAuthorization(
      current_client=Mock(id=self.client_id),
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=current_permission,
      ),
    )
    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.user_id
    assert auth.api_token == client_token
    assert auth.can_act_on_user(services, READ, self.user)
    assert auth.can_act_on_user(services, WRITE, self.user)
    assert auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
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
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)

  def test_role_private_experiments(self, services):
    current_user = Mock(id=self.user_id)

    client_token = Mock(
      all_experiments=True,
      guest_experiment_id=None,
      development=True,
      client_id=self.client_id,
    )

    current_membership = Mock(
      spec=Membership,
      user_id=self.user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.member,
      is_owner=False,
    )

    current_permission = Mock(
      spec=Permission,
      id=self.permission_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      user_id=self.user_id,
      can_read=True,
      can_write=True,
      can_admin=False,
      can_see_experiments_by_others=False,
    )

    auth = OrganizationMemberAuthorization(
      current_client=Mock(id=self.client_id),
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=current_permission,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.user_id
    assert auth.api_token == client_token
    assert auth.can_act_on_user(services, READ, self.user)
    assert auth.can_act_on_user(services, WRITE, self.user)
    assert auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
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
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert not auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert not auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert not auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)


class TestOrganizationOwnerAuthorization(BaseTestClientUserAuthorization):
  def test_role(self, services, client_token):
    current_user = Mock(id=self.user_id)
    current_membership = Mock(
      spec=Membership,
      user_id=self.user_id,
      organization_id=self.organization_id,
      membership_type=MembershipType.owner,
      is_owner=True,
    )
    auth = OrganizationOwnerAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id),
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      user_authorization=UserAuthorization(
        current_user=current_user,
        user_token=Mock(),
        scoped_membership=current_membership,
        scoped_permission=None,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user.id == self.user_id
    assert auth.api_token == client_token
    assert auth.can_act_on_user(services, READ, self.user)
    assert auth.can_act_on_user(services, WRITE, self.user)
    assert auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
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
    assert auth.can_act_on_experiment(services, READ, self.development_experiment)
    assert auth.can_act_on_experiment(services, WRITE, self.development_experiment)
    assert auth.can_act_on_experiment(services, ADMIN, self.development_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, READ, self.experiment_in_same_organization)
    assert auth.can_act_on_experiment(services, WRITE, self.experiment_in_same_organization)
    assert auth.can_act_on_experiment(services, ADMIN, self.experiment_in_same_organization)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert auth.can_act_on_project(services, READ, self.project_in_same_organization)
    assert auth.can_act_on_project(services, WRITE, self.project_in_same_organization)
    assert auth.can_act_on_project(services, ADMIN, self.project_in_same_organization)
