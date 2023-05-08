# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common.find import find
from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.user.model import normalize_email

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.connection import IntegrationTestConnection
from integration.utils.constants import NEW_USER_EMAIL_SEARCH_TERM, VERIFY_EMAIL_SEARCH_TERM
from integration.utils.emails import extract_signup_code
from integration.v1.endpoints.invites.test_base import InviteTestBase


class ClientInviteTestBase(InviteTestBase):
  @pytest.fixture(autouse=True)
  def check_invites(self, config_broker):
    if not config_broker.get("email.verify", True):
      pytest.skip("Since all users have verified emails, no invite object is created")

  def invite(self, connection, client_id, invitee, role, old_role=None):
    return self.invite_email(connection, client_id, invitee.email, role, old_role)

  def invite_email(self, connection, client_id, email, role, old_role=None):
    if old_role:
      return connection.clients(client_id).invites().create(email=email, role=role, old_role=old_role)
    return connection.clients(client_id).invites().create(email=email, role=role)

  def uninvite(self, connection, client_id, invitee):
    connection.clients(client_id).invites().delete(email=invitee.email)


class TestInvite(ClientInviteTestBase):
  # pylint: disable=too-many-public-methods
  def test_needs_invite(self, connection, client_id, invitee_connection):
    connection.clients(client_id).permissions().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(client_id).permissions().fetch()

  def test_invite_create(self, connection, client_id, config_broker):
    email = AuthProvider.randomly_generated_email()
    pending_permission = self.invite_email(connection, client_id, email, role=READ_ONLY_ROLE)

    assert pending_permission.email == normalize_email(email)
    assert pending_permission.role == READ_ONLY_ROLE
    assert pending_permission.client == client_id
    assert not pending_permission.invite_code

  def test_invite_no_verify(self, connection, client_id, invitee_connection, invitee, config_broker):
    if not self.email_needs_verify(config_broker):
      pytest.skip()

    self.invite(connection, client_id, invitee, role=READ_ONLY_ROLE)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(client_id).permissions().fetch()

  def test_verify(self, invitee_connection, invitee, inbox, config_broker):
    session = self.verify_email(invitee, invitee_connection, inbox, config_broker)
    assert session.user.has_verified_email
    assert invitee_connection.sessions().fetch().user.has_verified_email
    inbox.wait_for_email(invitee.email, search_term=NEW_USER_EMAIL_SEARCH_TERM)

  def test_duplicate_verify(self, invitee_connection, invitee, inbox, config_broker):
    invitee_connection.verifications().create(email=invitee.email)
    inbox.wait_for_email(invitee.email, search_term=VERIFY_EMAIL_SEARCH_TERM)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    inbox.wait_for_email(invitee.email, search_term=NEW_USER_EMAIL_SEARCH_TERM)
    invitee_connection.verifications().create(email=invitee.email)

  def test_invite_then_verify(self, connection, client_id, invitee_connection, invitee, inbox, config_broker, api):
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    invitee_connection.clients(client_id).permissions().fetch()

  def test_invite_deleted_user(
    self,
    connection,
    anonymous_connection,
    client_id,
    inbox,
    config_broker,
    auth_provider,
    api_url,
    api,
  ):
    # Make a user and then delete them
    password = AuthProvider.randomly_generated_password()
    deleted_invitee = auth_provider.create_user(password=password)
    deleted_invitee_token = auth_provider.create_user_token(deleted_invitee.id)
    deleted_invitee_connection = IntegrationTestConnection(api_url, user_token=deleted_invitee_token)
    deleted_invitee_connection.users(deleted_invitee.id).delete(password=password)
    inbox.reset()
    self.invite_email(connection, client_id, deleted_invitee.email, READ_ONLY_ROLE)

    recreated_user = anonymous_connection.users().create(
      name="Recreated user",
      password=AuthProvider.randomly_generated_password(),
      email=deleted_invitee.email,
    )
    self.verify_email(recreated_user, anonymous_connection, inbox, config_broker)
    permissions = connection.clients(client_id).permissions().fetch().data
    assert deleted_invitee.id not in [p.user.id for p in permissions]
    assert recreated_user.id in [p.user.id for p in permissions]

  def test_verify_then_invite(self, connection, client_id, invitee_connection, invitee, inbox, config_broker):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    invitee_connection.clients(client_id).permissions().fetch()

  def test_modify_invite(self, connection, client_id, invitee):
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    invite = self.invite(connection, client_id, invitee, ADMIN_ROLE, READ_ONLY_ROLE)
    assert invite.role == ADMIN_ROLE

  def test_uninvite(self, connection, client_id, invitee_connection, invitee, inbox, config_broker):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    invitee_connection.clients(client_id).permissions().fetch()
    self.uninvite(connection, client_id, invitee)

    # Invitee no longer has permissions
    assert invitee.id not in [r.user.id for r in connection.clients(client_id).permissions().fetch().iterate_pages()]

    # Invitee can't interact with client anymore
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(client_id).permissions().fetch()

    # Invitee's role token no longer works
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.as_client_only().clients(client_id).permissions().fetch()

  def test_cant_uninvite_owner(
    self,
    connection,
    owner,
    client_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, USER_ROLE)
    invitee_connection.clients(client_id).permissions().fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.uninvite(invitee_connection, client_id, owner)

  @pytest.mark.parametrize(
    "settings",
    [
      (ADMIN_ROLE, ADMIN_ROLE, (True, True, True)),
      (ADMIN_ROLE, USER_ROLE, (True, True, False)),
      (ADMIN_ROLE, READ_ONLY_ROLE, (True, False, False)),
    ],
  )
  def test_invite_permission_success(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee_connection,
    second_invitee,
    inbox,
    config_broker,
    settings,
  ):
    inviter_role, invitee_role, expected = settings
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      second_invitee_connection.clients(client_id).permissions().fetch()
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, role=inviter_role)
    self.invite(invitee_connection, client_id, second_invitee, role=invitee_role)
    all_permissions = second_invitee_connection.clients(client_id).permissions().fetch()
    per = find(all_permissions.data, lambda p: p.user.id == second_invitee.id)
    assert per and (per.can_read, per.can_write, per.can_admin) == expected

  @pytest.mark.parametrize(
    "settings",
    [
      (USER_ROLE, ADMIN_ROLE),
      (USER_ROLE, USER_ROLE),
      (USER_ROLE, READ_ONLY_ROLE),
      (READ_ONLY_ROLE, USER_ROLE),
      (READ_ONLY_ROLE, READ_ONLY_ROLE),
      (READ_ONLY_ROLE, USER_ROLE),
    ],
  )
  def test_invite_permission_fail(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee_connection,
    second_invitee,
    inbox,
    config_broker,
    settings,
  ):
    inviter_role, invitee_role = settings
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      second_invitee_connection.clients(client_id).permissions().fetch()
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, role=inviter_role)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.invite(invitee_connection, client_id, second_invitee, role=invitee_role)

  def test_invited_can_invite(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee_connection,
    second_invitee,
    inbox,
    config_broker,
  ):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      second_invitee_connection.clients(client_id).permissions().fetch()
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, ADMIN_ROLE)
    self.invite(invitee_connection, client_id, second_invitee, USER_ROLE)
    second_invitee_connection.clients(client_id).permissions().fetch()

  def test_uninvited_unverified_cant_invite(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee_connection,
    second_invitee,
    inbox,
    config_broker,
  ):
    if not self.email_needs_verify(config_broker):
      pytest.skip()
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, ADMIN_ROLE)
    self.invite(invitee_connection, client_id, second_invitee, USER_ROLE)
    self.uninvite(connection, client_id, invitee)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(client_id).permissions().fetch()
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      second_invitee_connection.clients(client_id).permissions().fetch()

  def test_uninvited_email_cant_invite(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    anonymous_connection,
    inbox,
    config_broker,
  ):
    second_email = AuthProvider.randomly_generated_email()
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, ADMIN_ROLE)
    self.invite_email(invitee_connection, client_id, second_email, USER_ROLE)
    self.uninvite(connection, client_id, invitee)
    anonymous_connection.verifications().create(email=second_email)
    invite_code = extract_signup_code(inbox, second_email)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      anonymous_connection.users().create(
        name="some name",
        email=second_email,
        password=AuthProvider.randomly_generated_password(),
        invite_code=invite_code,
      )

  def test_verify_email(self, invitee, invitee_connection, inbox, config_broker):
    code = self.get_email_verify_code(invitee, invitee_connection, inbox)
    self.do_verify_email(config_broker, code, invitee.email, invitee_connection)

  def test_verify_no_code(self, invitee, invitee_connection, config_broker):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.do_verify_email(config_broker, None, invitee.email, invitee_connection)

  def test_verify_invalid_code(self, invitee, invitee_connection, config_broker):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.do_verify_email(config_broker, "invalid_code", invitee.email, invitee_connection)

  def test_verify_no_email(self, invitee, invitee_connection, inbox, config_broker):
    code = self.get_email_verify_code(invitee, invitee_connection, inbox)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.do_verify_email(config_broker, code, None, invitee_connection)

  def test_verify_invalid_email(self, invitee, invitee_connection, inbox, config_broker):
    code = self.get_email_verify_code(invitee, invitee_connection, inbox)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.do_verify_email(config_broker, code, "differentemail@notsigopt.ninja", invitee_connection)

  def test_invite_creates_membership(
    self, services, connection, client_id, invitee_connection, invitee, inbox, config_broker, api
  ):
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    client = services.client_service.find_by_id(client_id)
    user_id = int(invitee.id)
    membership = services.membership_service.find_by_user_and_organization(
      user_id=user_id, organization_id=client.organization_id
    )
    assert membership is not None
    assert membership.user_id == user_id
    assert membership.organization_id == client.organization_id

  def test_invite_creates_pending_permissions(
    self, services, connection, client_id, invitee_connection, invitee, inbox, config_broker, api
  ):
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    pending_permissions_for_client = services.pending_permission_service.find_by_client_id(client_id)
    assert len(pending_permissions_for_client) == 1
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    pending_permissions_for_client = services.pending_permission_service.find_by_client_id(client_id)
    assert len(pending_permissions_for_client) == 0

  def test_uninvite_deletes_membership(
    self, services, connection, client_id, invitee_connection, invitee, inbox, config_broker, api
  ):
    self.invite(connection, client_id, invitee, READ_ONLY_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    client = services.client_service.find_by_id(client_id)
    self.uninvite(connection, client_id, invitee)
    membership = services.membership_service.find_by_user_and_organization(invitee.id, client.organization_id)
    assert membership is None


class TestInviteLimits(ClientInviteTestBase):
  # Overrides connection in test_base with function scope
  @classmethod
  @pytest.fixture
  def connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider)

  def test_can_invite_without_limit(self, connection, client_id, organization_id):
    self.invite_email(connection, client_id, AuthProvider.randomly_generated_email(), USER_ROLE)

  def test_can_create_without_limit(self, connection, client_id, organization_id):
    self.invite_email(connection, client_id, AuthProvider.randomly_generated_email(), USER_ROLE)

  def test_invite_invited_raises_exception(self, connection, client_id, invitee, config_broker):
    self.invite(connection, client_id, invitee, USER_ROLE)
    with RaisesApiException(HTTPStatus.CONFLICT):
      self.invite(connection, client_id, invitee, USER_ROLE)

  def test_can_invite_existing(self, services, connection, client_id, config_broker):
    email = AuthProvider.randomly_generated_email()
    self.invite_email(connection, client_id, email, USER_ROLE)
    with RaisesApiException(HTTPStatus.CONFLICT):
      self.invite_email(connection, client_id, email, USER_ROLE)

  def test_can_use_invalid_invites(
    self,
    services,
    connection,
    client_id,
    invitee,
    invitee_connection,
    inbox,
    config_broker,
  ):
    self.invite(connection, client_id, invitee, USER_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)


class TestPermissionChange(ClientInviteTestBase):
  def change_role(self, connection, client_id, invitee, old_role, new_role):
    connection.clients(client_id).invites().create(email=invitee.email, role=new_role, old_role=old_role)

  def test_demote_user(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee,
    second_invitee_connection,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)

    self.invite(connection, client_id, invitee, ADMIN_ROLE)
    self.invite(invitee_connection, client_id, second_invitee, ADMIN_ROLE)

    client_permission = connection.clients(client_id).permissions().fetch()
    per = find(client_permission.data, lambda p: p.user.id == second_invitee.id)
    assert per and (per.can_read, per.can_write, per.can_admin) == (True, True, True)

    self.change_role(invitee_connection, client_id, second_invitee, old_role=ADMIN_ROLE, new_role=USER_ROLE)

    client_permission = connection.clients(client_id).permissions().fetch()
    per = find(client_permission.data, lambda p: p.user.id == second_invitee.id)
    assert per and (per.can_read, per.can_write, per.can_admin) == (True, True, False)

  def test_promote_user(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee,
    second_invitee_connection,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)

    self.invite(connection, client_id, invitee, ADMIN_ROLE)
    self.invite(invitee_connection, client_id, second_invitee, READ_ONLY_ROLE)

    client_permission = connection.clients(client_id).permissions().fetch()
    per = find(client_permission.data, lambda p: p.user.id == second_invitee.id)
    assert per and (per.can_read, per.can_write, per.can_admin) == (True, False, False)

    # with wrong information passed in initially
    with RaisesApiException(HTTPStatus.CONFLICT):
      self.change_role(invitee_connection, client_id, second_invitee, old_role=USER_ROLE, new_role=ADMIN_ROLE)

    self.change_role(invitee_connection, client_id, second_invitee, old_role=READ_ONLY_ROLE, new_role=ADMIN_ROLE)

    client_permission = connection.clients(client_id).permissions().fetch()
    per = find(client_permission.data, lambda p: p.user.id == second_invitee.id)
    assert per and (per.can_read, per.can_write, per.can_admin) == (True, True, True)

  @pytest.mark.parametrize("role", [USER_ROLE, READ_ONLY_ROLE])
  def test_user_cannot_modify_role(
    self,
    connection,
    client_id,
    invitee_connection,
    invitee,
    second_invitee,
    second_invitee_connection,
    inbox,
    config_broker,
    role,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.verify_email(second_invitee, second_invitee_connection, inbox, config_broker)
    self.invite(connection, client_id, invitee, role)
    self.invite(connection, client_id, second_invitee, READ_ONLY_ROLE)

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.change_role(invitee_connection, client_id, second_invitee, old_role=READ_ONLY_ROLE, new_role=ADMIN_ROLE)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.change_role(invitee_connection, client_id, second_invitee, old_role=READ_ONLY_ROLE, new_role=USER_ROLE)

  def test_invites_by_non_owner(
    self,
    owner_connection_same_organization,
    write_connection_same_client,
    read_connection_same_client,
    admin_connection_same_client,
    auth_provider,
  ):
    client_id = owner_connection_same_organization.client_id

    # Read/write users cannot invite users
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      write_connection_same_client.clients(client_id).invites().create(
        email=auth_provider.randomly_generated_email(),
        role=READ_ONLY_ROLE,
        old_role=NO_ROLE,
      )

    # Admin users can invite outsiders to be admins
    outsider_email = auth_provider.randomly_generated_email()
    auth_provider.create_user_tokens(email=outsider_email)
    admin_connection_same_client.clients(client_id).invites().create(
      email=outsider_email,
      role=ADMIN_ROLE,
      old_role=NO_ROLE,
    )

    # Owners can invite outsiders to be admins
    outsider_email = auth_provider.randomly_generated_email()
    auth_provider.create_user_tokens(email=outsider_email)
    owner_connection_same_organization.clients(client_id).invites().create(
      email=outsider_email,
      role=ADMIN_ROLE,
      old_role=NO_ROLE,
    )
