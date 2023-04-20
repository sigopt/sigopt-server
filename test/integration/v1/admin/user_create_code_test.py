# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, READ_ONLY_ROLE
from zigopt.membership.model import MembershipType

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.utils.emails import extract_signup_code
from integration.v1.test_base import V1Base


class TestUserCreateCode(V1Base):
  def set_org_admin(self, user_id, client_id, org_admin=False):
    permission = self.services.permission_service.find_by_client_and_user(client_id, user_id)
    if not permission.can_admin:
      permission_meta = self.services.permission_service.set_permission_meta(
        permission=permission,
        can_admin=org_admin,
        can_write=None,
        can_read=None,
        can_see_experiments_by_others=None,
      )
      self.services.permission_service.update_meta(permission, permission_meta)

  def invite_user_as_role_and_get_code(self, connection, connection_id, email, inbox, config_broker, **kwargs):
    role = kwargs.get("role")
    connection(connection_id).invites().create(
      email=email,
      old_role=NO_ROLE,
      **kwargs,
    )
    invite_code = extract_signup_code(inbox, email)
    if role == MembershipType.owner and invite_code is None:
      assert config_broker.get("email.verify") is False
      assert config_broker.get("email.enabled") is False
      pytest.skip()
    return invite_code

  def invite_owner_and_get_code(self, api_connection, email, inbox, config_broker):
    return self.invite_user_as_role_and_get_code(
      api_connection.organizations,
      api_connection.organization_id,
      email,
      inbox,
      config_broker,
      membership_type=MembershipType.owner.value,
    )

  def invite_and_get_code(self, api_connection, email, inbox, config_broker):
    return self.invite_user_as_role_and_get_code(
      api_connection.clients, api_connection.client_id, email, inbox, config_broker, role=READ_ONLY_ROLE
    )

  def invite_admin_and_get_code(self, api_connection, email, inbox, config_broker):
    return self.invite_user_as_role_and_get_code(
      api_connection.clients, api_connection.client_id, email, inbox, config_broker, role=ADMIN_ROLE
    )

  def invite_owner(self, owner_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    code = self.invite_owner_and_get_code(owner_connection, email, inbox, config_broker)
    return code

  def invite_admin(self, owner_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    code = self.invite_admin_and_get_code(owner_connection, email, inbox, config_broker)
    return code

  @pytest.mark.slow
  def test_inviter_is_org_admin(self, connection, anonymous_connection, inbox, config_broker):
    self.set_org_admin(
      user_id=connection.user_id,
      client_id=connection.client_id,
      org_admin=True,
    )
    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    code = self.invite_and_get_code(connection, email, inbox, config_broker)
    user = anonymous_connection.users().create(
      name="Some user",
      email=email,
      password=password,
      invite_code=code,
    )
    session = anonymous_connection.sessions().create(email=email, password=password)
    assert session.user.id == user.id
    assert session.client.id == connection.client_id
    self.set_org_admin(
      user_id=connection.user_id,
      client_id=connection.client_id,
      org_admin=False,
    )

  def test_cant_create_owner_if_inviter_not_owner(self, owner_connection, anonymous_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    code = self.invite_owner_and_get_code(owner_connection, email, inbox, config_broker)
    self.services.membership_service.delete_by_organization_and_user(
      organization_id=owner_connection.organization_id,
      user_id=owner_connection.user_id,
    )
    self.services.membership_service.create_if_not_exists(
      user_id=owner_connection.user_id,
      organization_id=owner_connection.organization_id,
      membership_type=MembershipType.member,
    )
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      anonymous_connection.users().create(
        name="Some user",
        email=email,
        password=password,
        invite_code=code,
      )
    membership = self.services.membership_service.find_by_user_and_organization(
      user_id=owner_connection.user_id,
      organization_id=owner_connection.organization_id,
    )
    self.services.membership_service.elevate_to_owner(membership)
    assert self.services.membership_service.user_is_owner_for_organization(
      user_id=owner_connection.user_id, organization_id=owner_connection.organization_id
    )

  def test_invite_owner_no_limits(self, owner_connection, inbox, config_broker):
    code = self.invite_owner(owner_connection, inbox, config_broker)
    assert code

  def test_invite_admin_no_limits(self, owner_connection, inbox, config_broker):
    code = self.invite_admin(owner_connection, inbox, config_broker)
    assert code

  @pytest.mark.slow
  def test_create_owner_code(self, owner_connection, anonymous_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    code = self.invite_owner_and_get_code(owner_connection, email, inbox, config_broker)
    user = anonymous_connection.users().create(
      name="Some user",
      email=email,
      password=password,
      invite_code=code,
    )
    session = anonymous_connection.sessions().create(email=email, password=password)
    assert session.user.id == user.id
    assert session.client.to_json()["organization"] == owner_connection.organization_id

  @pytest.mark.slow
  def test_create_code(self, owner_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    code = self.invite_and_get_code(owner_connection, email, inbox, config_broker)
    user = owner_connection.users().create(
      name="Some user",
      email=email,
      password=password,
      invite_code=code,
    )
    session = owner_connection.sessions().create(email=email, password=password)
    assert session.user.id == user.id
    assert session.client.id == owner_connection.client_id

  def test_create_uninvite(self, connection, anonymous_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    code = self.invite_and_get_code(connection, email, inbox, config_broker)
    connection.clients(connection.client_id).invites().delete(email=email)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        name="Some user",
        email=email,
        password=password,
        invite_code=code,
      )

  def test_create_invite_wrong_email(self, connection, anonymous_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    other_email = "abc" + email
    password = AuthProvider.randomly_generated_password()
    code = self.invite_and_get_code(connection, email, inbox, config_broker)
    with RaisesApiException(HTTPStatus.CONFLICT):
      anonymous_connection.users().create(
        name="Some user",
        email=other_email,
        password=password,
        invite_code=code,
      )

  def test_create_invalid_code(self, anonymous_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        name="",
        password=AuthProvider.randomly_generated_password(),
        invite_code="somefakecode",
      )
