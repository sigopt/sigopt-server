# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.endpoints.invites.test_base import InviteTestBase


class TestUserPermissionsList(InviteTestBase):
  @pytest.fixture
  def client(self, owner_connection):
    return owner_connection.organizations(owner_connection.organization_id).clients().create(name="Test client")

  @pytest.fixture
  def other_client(self, owner_connection, client):
    return owner_connection.organizations(owner_connection.organization_id).clients().create(name="Other client")

  @pytest.fixture(autouse=True)
  def organization(self, owner_connection, client):
    return owner_connection.organizations(owner_connection.organization_id).update(
      allow_signup_from_email_domains=True,
      email_domains=["notsigopt.ninja"],
      client_for_email_signup=client.id,
    )

  def test_request_permission(self, invitee, invitee_connection, client, inbox, config_broker):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(client.id).fetch()
    invitee_connection.users(invitee_connection.user_id).permissions().create(client=client.id)
    invitee_connection.clients(client.id).fetch()

  def test_must_provide_client(self, invitee, invitee_connection, client, inbox, config_broker):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      invitee_connection.users(invitee_connection.user_id).permissions().create()

  def test_must_verify_email(self, invitee, invitee_connection, client):
    assert invitee.has_verified_email is False
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      invitee_connection.users(invitee_connection.user_id).permissions().create(client=client.id)

  def test_incorrect_client(self, invitee, invitee_connection, other_client, inbox, config_broker):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      invitee_connection.users(invitee_connection.user_id).permissions().create(client=other_client.id)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      invitee_connection.users(invitee_connection.user_id).permissions().create(client="-1")

  def test_email_signup_disabled(
    self,
    invitee,
    invitee_connection,
    owner_connection,
    organization,
    client,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    owner_connection.organizations(organization.id).update(allow_signup_from_email_domains=False)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      invitee_connection.users(invitee_connection.user_id).permissions().create(client=client.id)

  def test_incorrect_email_domain(
    self,
    invitee,
    invitee_connection,
    owner_connection,
    organization,
    client,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    owner_connection.organizations(organization.id).update(email_domains=["sigopt.ninja"])
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      invitee_connection.users(invitee_connection.user_id).permissions().create(client=client.id)
