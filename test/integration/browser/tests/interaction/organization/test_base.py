# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.client.model import Client
from zigopt.invite.constant import ADMIN_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.membership.model import MembershipType
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN

from integration.browser.tests.browser_test import BrowserTest
from integration.utils.random_email import generate_random_email
from integration.web.test_base import LoginState


class OrganizationTestBase(BrowserTest):
  def _make_user(self, services, membership_type, client_invites, api_connection, auth_provider, name=None):
    user = auth_provider.create_user(name=name, has_verified_email=True)
    self._make_invite(membership_type, client_invites, api_connection, email=user.email)
    # NOTE: make sure that the user has another membership
    services.membership_service.create_if_not_exists(
      user_id=int(user.id),
      organization_id=1,
      membership_type=MembershipType.owner,
    )
    return user

  def _make_invite(self, membership_type, client_invites, api_connection, email=None):
    return (
      api_connection.organizations(api_connection.organization_id)
      .invites()
      .create(
        email=email or generate_random_email(),
        membership_type=membership_type.value,
        client_invites=client_invites,
      )
    )

  @classmethod
  @pytest.fixture(scope="function")
  def member_login_state(cls, auth_provider, login_state):
    email = auth_provider.randomly_generated_email()
    password = auth_provider.randomly_generated_password()
    user = auth_provider.create_user(
      email=email,
      password=password,
      name="</script>Integration Test Member",
      has_verified_email=True,
    )
    user_token = auth_provider.create_user_token(user.id)
    user_id = int(user.id)
    auth_provider.create_membership(user_id, login_state.organization_id)
    auth_provider.create_permission(user_id, login_state.client_id, ADMIN)
    client_token = auth_provider.create_client_token(login_state.client_id, user_id)
    return LoginState(
      email.lower(),
      password,
      user_id,
      user_token,
      login_state.client_id,
      login_state.organization_id,
      client_token,
    )

  @pytest.fixture
  def owner_invite(self, api_connection):
    return self._make_invite(MembershipType.owner, [], api_connection)

  @pytest.fixture
  def member_invite(self, api_connection):
    return self._make_invite(
      MembershipType.member,
      [
        dict(
          id=api_connection.client_id,
          role=USER_ROLE,
        )
      ],
      api_connection,
    )

  @pytest.fixture
  def owner_user(self, services, api_connection, auth_provider):
    return self._make_user(
      services,
      MembershipType.owner,
      [],
      api_connection,
      auth_provider,
    )

  def make_read_user(self, services, api_connection, auth_provider):
    return self._make_user(
      services,
      MembershipType.member,
      [
        dict(
          id=api_connection.client_id,
          role=READ_ONLY_ROLE,
        )
      ],
      api_connection,
      auth_provider,
    )

  @pytest.fixture
  def read_user(self, services, api_connection, auth_provider):
    return self.make_read_user(
      services,
      api_connection,
      auth_provider,
    )

  @pytest.fixture
  def write_user(self, services, api_connection, auth_provider):
    return self._make_user(
      services,
      MembershipType.member,
      [
        dict(
          id=api_connection.client_id,
          role=USER_ROLE,
        )
      ],
      api_connection,
      auth_provider,
    )

  @pytest.fixture
  def admin_user(self, services, api_connection, auth_provider):
    return self._make_user(
      services,
      MembershipType.member,
      [
        dict(
          id=api_connection.client_id,
          role=ADMIN_ROLE,
        )
      ],
      api_connection,
      auth_provider,
    )

  @pytest.fixture
  def another_client(self, api_connection, services):
    client = Client(
      name="Second Client",
      organization_id=int(api_connection.organization_id),
    )
    services.client_service.insert(client)
    services.project_service.create_example_for_client(client_id=client.id)
    return client
