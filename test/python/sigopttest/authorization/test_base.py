# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.membership.model import MembershipType
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta

from sigopttest.base.utils import generate_ids


def dummy_find_role_by_client_and_user(*roles):
  def find_function(client_id, user_id):
    for role in roles:
      if role.client_id == client_id and role.user_id == user_id:
        return role
    return None

  return find_function


def dummy_find_role_by_user_ids(*roles):
  def find_function(user_ids):
    found_roles = []
    for role in roles:
      for user_id in user_ids:
        if role.user_id == user_id:
          found_roles.append(role)
    if len(found_roles) > 0:
      return found_roles
    return None

  return find_function


def dummy_find_experiment_by_id(*experiments):
  def find_function(experiment_id, include_deleted=False):
    for experiment in experiments:
      if experiment.id == experiment_id:
        return experiment
    return None

  return find_function


def dummy_find_client_by_id(*clients):
  def find_function(client_id):
    for client in clients:
      if client.id == client_id:
        return client
    return None

  return find_function


def dummy_find_organization_by_id(*organizations):
  def find_function(organization_id):
    for organization in organizations:
      if organization.id == organization_id:
        return organization
    return None

  return find_function


def dummy_find_membership_by_user_and_organization(*memberships):
  def find_function(user_id, organization_id):
    for membership in memberships:
      if membership.user_id == user_id and membership.organization_id == organization_id:
        return membership
    return None

  return find_function


class _TestAuthorizationCore:
  ids = iter(generate_ids())
  organization = Mock(
    id=next(ids),
  )
  organization_id = organization.id
  client = Mock(
    id=next(ids),
    organization_id=organization_id,
  )
  client_id = client.id
  client_in_same_organization = Mock(
    id=next(ids),
    organization_id=organization_id,
  )
  client_in_same_organization_id = client_in_same_organization.id
  private_organization = Mock(id=next(ids))
  private_client = Mock(
    id=next(ids),
    organization_id=private_organization.id,
    allow_users_to_see_experiments_by_others=False,
  )
  private_client_id = private_client.id
  other_organization = Mock(
    id=next(ids),
  )
  other_organization_id = other_organization.id
  other_client = Mock(
    id=next(ids),
    organization_id=other_organization_id,
  )
  other_client_id = other_client.id
  user = Mock(id=next(ids))
  user_id = user.id
  non_owner_user = Mock(id=next(ids))
  non_owner_user_id = non_owner_user.id
  user_in_same_organization = Mock(id=next(ids))
  user_in_same_organization_id = user_in_same_organization.id
  other_user = Mock(id=next(ids))
  other_user_id = other_user.id
  user_with_same_client_for_role = Mock(id=next(ids))
  user_id_with_same_client_for_role = user_with_same_client_for_role.id
  user_with_no_role = Mock(id=next(ids))
  permission_id = next(ids)
  project = Mock(
    id=next(ids),
    reference_id="project",
    client_id=client_id,
    created_by=user_id,
  )
  project_in_same_organization = Mock(
    id=next(ids),
    reference_id="project",
    client_id=client_in_same_organization_id,
    created_by=user_id,
  )
  experiment = Mock(
    id=next(ids),
    client_id=client_id,
    development=False,
    created_by=user_id,
    project_id=project.id,
  )
  experiment_in_same_organization = Mock(
    id=next(ids),
    client_id=client_in_same_organization_id,
    development=False,
    created_by=user_id,
    project_id=project_in_same_organization.id,
  )
  token = Mock(id=next(ids))
  development_experiment = Mock(
    id=next(ids),
    client_id=client_id,
    development=True,
    created_by=user_id,
    project_id=None,
  )
  another_experiment_with_client = Mock(
    id=next(ids),
    client_id=client_id,
    development=False,
    created_by=other_user_id,
    project_id=None,
  )
  other_experiment = Mock(
    id=next(ids),
    client_id=other_client_id,
    development=False,
    project_id=None,
  )
  experiment_private_client = Mock(
    id=next(ids),
    client_id=private_client_id,
    created_by=user_id,
    project_id=None,
  )
  other_experiment_private_client = Mock(
    id=next(ids),
    client_id=private_client_id,
    created_by=other_user_id,
    project_id=None,
  )
  another_project_with_client = Mock(
    id=next(ids),
    reference_id="project2",
    client_id=client_id,
    created_by=other_user_id,
  )
  other_project = Mock(
    id=next(ids),
    reference_id="project",
    client_id=other_client_id,
  )
  project_private_client = Mock(
    id=next(ids),
    reference_id="project",
    client_id=private_client_id,
    created_by=user_id,
  )
  other_project_private_client = Mock(
    id=next(ids),
    reference_id="project2",
    client_id=private_client_id,
    created_by=other_user_id,
  )

  membership = Mock(
    user_id=user_id,
    organization_id=organization_id,
    membership_type=MembershipType.owner,
    is_owner=True,
  )
  non_owner_user_membership = Mock(
    user_id=non_owner_user_id,
    organization_id=organization_id,
    membership_type=MembershipType.member,
    is_owner=False,
  )
  user_in_same_organization_membership = Mock(
    user_id=user_in_same_organization_id,
    organization_id=organization_id,
    membership_type=MembershipType.member,
    is_owner=False,
  )
  other_user_membership = Mock(
    user_id=other_user_id,
    organization_id=other_organization_id,
    membership_type=MembershipType.member,
    is_owner=False,
  )
  private_organization_membership = Mock(
    user_id=user_id,
    organization_id=private_organization.id,
    membership_type=MembershipType.member,
    is_owner=False,
  )
  permission_meta = PermissionMeta()
  permission_meta.can_admin = True
  permission_meta.can_write = True
  permission_meta.can_read = True
  current_client_non_owner_user_role = Permission(
    client_id=client_id, user_id=non_owner_user_id, organization_id=organization_id, permission_meta=permission_meta
  )
  current_client_different_user_role = Permission(
    client_id=client_id,
    user_id=user_id_with_same_client_for_role,
    organization_id=organization_id,
    permission_meta=permission_meta,
  )
  other_client_other_user_role = Permission(
    client_id=other_client_id, user_id=other_user_id, organization_id=organization_id, permission_meta=permission_meta
  )

  private_permission_meta = PermissionMeta()
  private_permission_meta.can_admin = False
  private_permission_meta.can_read = True
  private_permission_meta.can_write = True
  private_permission_meta.can_see_experiments_by_others = False
  private_client_user_role = Permission(
    client_id=private_client_id,
    user_id=user_id,
    organization_id=organization_id,
    permission_meta=private_permission_meta,
  )

  @pytest.fixture
  def services(self):
    return self.make_services()

  def make_services(self):
    return Mock(
      experiment_service=Mock(
        find_by_id=dummy_find_experiment_by_id(
          self.experiment,
          self.experiment_in_same_organization,
          self.another_experiment_with_client,
          self.other_experiment,
        )
      ),
      invite_service=Mock(can_have_membership_to_organization=Mock(return_value=True)),
      membership_service=Mock(
        find_owners_by_user_id=lambda user_id: ([self.membership] if user_id == self.user_id else None),
        find_by_user_and_organization=dummy_find_membership_by_user_and_organization(
          self.membership,
          self.non_owner_user_membership,
          self.user_in_same_organization_membership,
          self.other_user_membership,
          self.private_organization_membership,
        ),
        users_are_mutually_visible=lambda user1_id, user2_id: (
          user1_id == self.membership.user_id
          and user2_id
          in (
            self.user_id,
            self.user_id_with_same_client_for_role,
            self.non_owner_user_id,
            self.user_in_same_organization_id,
          )
        ),
        user_is_owner_for_client=lambda user_id, client_id: (
          self.membership.user_id == user_id and client_id in (self.client_id, self.client_in_same_organization_id)
        ),
      ),
      permission_service=Mock(
        find_by_client_and_user=dummy_find_role_by_client_and_user(
          self.current_client_non_owner_user_role,
          self.current_client_different_user_role,
          self.other_client_other_user_role,
          self.private_client_user_role,
        ),
        find_by_user_ids=dummy_find_role_by_user_ids(
          self.current_client_non_owner_user_role,
          self.current_client_different_user_role,
          self.other_client_other_user_role,
          self.private_client_user_role,
        ),
      ),
      client_service=Mock(
        find_by_id=dummy_find_client_by_id(
          self.client,
          self.client_in_same_organization,
          self.other_client,
          self.private_client,
        ),
        user_is_owner_for_client=lambda user_id, client_id: (
          user_id == self.membership.user_id
          and client_id
          in (
            self.client_id,
            self.client_in_same_organization_id,
          )
        ),
      ),
      organization_service=Mock(
        find_by_id=dummy_find_organization_by_id(self.organization, self.private_organization, self.other_organization),
      ),
    )
