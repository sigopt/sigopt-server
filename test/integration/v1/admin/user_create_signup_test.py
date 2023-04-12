# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.user.model import get_domain_from_email

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.connection import IntegrationTestConnection
from integration.v1.test_base import V1Base


class TestUserCreateSignup(V1Base):
  @pytest.fixture(autouse=True)
  def require_signup(self, config_broker):
    if config_broker.get("features.requireInvite"):
      pytest.skip()

  def check_client(self, services, user, client):
    client_obj = services.client_service.find_by_id(int(client.id))
    assert client_obj is not None
    assert client_obj.name == client.name

    organization_obj = services.organization_service.find_by_id(client_obj.organization_id)
    assert organization_obj is not None
    assert organization_obj.name == client.name

    membership_obj = services.membership_service.find_by_user_and_organization(
      user_id=int(user.id),
      organization_id=organization_obj.id,
    )
    assert membership_obj is not None
    assert membership_obj.user_id == int(user.id)
    assert membership_obj.organization_id == organization_obj.id

  def test_create(self, services, anonymous_connection, inbox, config_broker):
    client_name = "here is a client name"
    user = anonymous_connection.users().create(
      name="Some user",
      email=AuthProvider.randomly_generated_email(),
      password=AuthProvider.randomly_generated_password(),
      client_name=client_name,
    )
    session = self.verify_email(user, anonymous_connection, inbox, config_broker)
    assert session.user.id == user.id
    assert session.client is not None
    assert session.client.name == client_name

    self.check_client(services, user, session.client)

  def test_create_needs_verify(self, anonymous_connection, inbox, config_broker):
    if config_broker.get("email.verify") is False:
      pytest.skip()

    email = AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    anonymous_connection.users().create(
      name="Some user",
      email=email,
      password=password,
      client_name="here is a client name",
    )
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      assert anonymous_connection.sessions().create(email=email, password=password)

  def test_create_client_name(self, anonymous_connection):
    assert (
      anonymous_connection.users()
      .create(
        name="Some user",
        email=AuthProvider.randomly_generated_email(),
        password=AuthProvider.randomly_generated_password(),
        client_name="Client name",
      )
      .id
      is not None
    )

  def test_create_invalid_email(self, anonymous_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        name="Some user",
        password=AuthProvider.randomly_generated_password(),
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email="",
        name="Some user",
        password=AuthProvider.randomly_generated_password(),
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email="notanemail",
        name="Some user",
        password=AuthProvider.randomly_generated_password(),
      )

  def test_create_invalid_password(self, anonymous_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        name="Some user",
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        name="Some user",
        password="",
      )

  def test_create_invalid_name(self, anonymous_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        password=AuthProvider.randomly_generated_password(),
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        name="",
        password=AuthProvider.randomly_generated_password(),
      )

  def test_create_invalid_client_name(self, anonymous_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.users().create(
        email=AuthProvider.randomly_generated_email(),
        password=AuthProvider.randomly_generated_password(),
        client_name="",
      )

  def test_cant_create_user_twice(self, connection):
    user = connection.users(connection.user_id).fetch()
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.users().create(name="Some user", email=user.email, password="password")


class TestUserCreateOrgSignup(V1Base):
  @pytest.fixture
  def organization_id(self, owner_connection):
    return owner_connection.organization_id

  @pytest.fixture
  def client_for_email_signup_id(self, owner_connection):
    assert owner_connection.client_id
    return owner_connection.client_id

  @pytest.fixture
  def signup_connection(self, owner_connection, api_url, api):
    token = owner_connection.clients(owner_connection.client_id).tokens().create().token
    return IntegrationTestConnection(api_url, client_token=token)

  @pytest.fixture(autouse=True)
  def setup_org(self, owner_connection, organization_id, client_for_email_signup_id):
    owner_connection.organizations(organization_id).update(
      email_domains=[get_domain_from_email(AuthProvider.randomly_generated_email())],
      allow_signup_from_email_domains=True,
      client_for_email_signup=client_for_email_signup_id,
    )

  def create_user(self, signup_connection, client_id, email=None):
    email = email or AuthProvider.randomly_generated_email()
    return signup_connection.users().create(
      name=email,
      email=email,
      password=AuthProvider.randomly_generated_password(),
      client=client_id,
    )

  def login(self, user, signup_connection, inbox, config_broker):
    return self.verify_email(user, signup_connection, inbox, config_broker)

  def create_and_test_connection(self, session, api_url, api, organization_id):
    connection = IntegrationTestConnection(api_url, user_token=session.api_token.token)
    connection.organizations(organization_id).fetch()
    return connection

  def test_create_into_org(
    self,
    signup_connection,
    organization_id,
    client_for_email_signup_id,
    inbox,
    config_broker,
    api_url,
    api,
  ):
    user = self.create_user(signup_connection, client_for_email_signup_id)
    session = self.login(user, signup_connection, inbox, config_broker)
    assert session.client.id == client_for_email_signup_id
    connection = self.create_and_test_connection(session, api_url, api, organization_id)
    (membership,) = connection.users(session.user.id).memberships().fetch().iterate_pages()
    assert membership.organization.id == organization_id
    assert membership.type == "member"
    (permission,) = connection.users(session.user.id).permissions().fetch().iterate_pages()
    assert permission.can_admin is False
    assert permission.can_write is True
    assert permission.can_read is True
    assert permission.client.id == client_for_email_signup_id
    assert permission.is_owner is False

  def test_require_client_auth_to_signup(self, anonymous_connection, client_for_email_signup_id):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.create_user(anonymous_connection, client_for_email_signup_id)

  def test_forbid_signup(self, signup_connection, owner_connection, organization_id, client_for_email_signup_id):
    owner_connection.organizations(organization_id).update(allow_signup_from_email_domains=False)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.create_user(signup_connection, client_for_email_signup_id)

  def test_invalid_email_domain(self, signup_connection, owner_connection, organization_id, client_for_email_signup_id):
    owner_connection.organizations(organization_id).update(email_domains=["mydomain.com"])
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.create_user(signup_connection, client_for_email_signup_id, email="attacker@fake.mydomain.com")

  def test_incorrect_client_id(
    self,
    signup_connection,
    owner_connection,
    organization_id,
  ):
    other_client = owner_connection.organizations(organization_id).clients().create(name="Some other client")
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.create_user(signup_connection, other_client.id)

  def test_expired_signup_link(
    self,
    signup_connection,
    owner_connection,
    organization_id,
    client_for_email_signup_id,
    inbox,
    config_broker,
    api_url,
    api,
  ):
    user = self.create_user(signup_connection, client_for_email_signup_id)
    owner_connection.organizations(organization_id).update(allow_signup_from_email_domains=False)
    session = self.login(user, signup_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      self.create_and_test_connection(session, api_url, api, organization_id)

  def test_changed_email_domains(
    self,
    signup_connection,
    owner_connection,
    organization_id,
    client_for_email_signup_id,
    inbox,
    config_broker,
    api_url,
    api,
  ):
    user = self.create_user(signup_connection, client_for_email_signup_id)
    owner_connection.organizations(organization_id).update(email_domains=["someotherdomain.com"])
    session = self.login(user, signup_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      self.create_and_test_connection(session, api_url, api, organization_id)

  def test_changed_client_signup_link(
    self,
    signup_connection,
    owner_connection,
    organization_id,
    client_for_email_signup_id,
    inbox,
    config_broker,
    api_url,
    api,
  ):
    other_client = owner_connection.organizations(organization_id).clients().create(name="Some other client")
    user = self.create_user(signup_connection, client_for_email_signup_id)
    owner_connection.organizations(organization_id).update(client_for_email_signup=other_client.id)
    session = self.login(user, signup_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      self.create_and_test_connection(session, api_url, api, organization_id)
