# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.api.auth import _api_token_authentication as api_token_authentication
from zigopt.api.auth import _client_token_authentication as client_token_authentication
from zigopt.api.auth import _maybe_client_token_authentication as maybe_client_token_authentication
from zigopt.api.auth import _user_token_authentication as user_token_authentication
from zigopt.membership.model import Membership, MembershipType
from zigopt.net.errors import ForbiddenError, UnauthorizedError

from sigopttest.base.config_broker import StrictAccessConfigBroker
from sigopttest.base.utils import generate_ids


def dummy_find_client_by_id(*clients):
  def find_function(client_id, include_deleted=False):
    for client in clients:
      if client.id == client_id:
        if not client.deleted:
          return client
        elif include_deleted:
          return client
    return None

  return find_function


def dummy_find_token_by_token_value(*tokens):
  def find_function(token, include_expired=False):
    for t in tokens:
      if t.token == token:
        if not t.expired:
          return t
        elif include_expired:
          return t
        else:
          return None
    return None

  return find_function


def dummy_find_user_by_id(*users):
  def find_function(user_id, include_deleted=False):
    for user in users:
      if user.id == user_id:
        if not user.deleted:
          return user
        elif include_deleted:
          return user
    return None

  return find_function


class _TestAuthCore:
  ids = iter(generate_ids())
  organization = Mock(id=next(ids))
  client = Mock(id=next(ids), organization_id=organization.id, deleted=False)
  client_token = Mock(
    client_id=client.id,
    token="client_token_value",
    user_id=None,
    is_client_token=True,
    is_user_token=False,
    expired=False,
  )
  deleted_client = Mock(id=next(ids), organization_id=organization.id, deleted=True)
  deleted_client_token = Mock(
    client_id=deleted_client.id, token="deleted_client_token_value", is_client_token=True, is_user_token=False
  )
  orphan_client_token = Mock(client_id=6, token="orphan_client_token_value", is_client_token=True, is_user_token=False)
  user = Mock(id=next(ids), deleted=False)
  user_token = Mock(user_id=user.id, token="user_token_value", is_client_token=False, is_user_token=True, expired=False)
  deleted_user = Mock(id=next(ids), deleted=True)
  deleted_user_token = Mock(
    user_id=deleted_user.id, token="deleted_user_token_value", is_client_token=False, is_user_token=True
  )
  orphan_user_token = Mock(
    user_id=next(ids), token="orphan_user_token_value", is_client_token=False, is_user_token=True
  )
  bad_token = "bad_token"
  role_token = Mock(
    client_id=client.id,
    token="role_token_value",
    user_id=user.id,
    is_client_token=True,
    is_user_token=False,
    expired=False,
  )
  deleted_user_role_token = Mock(
    client_id=client.id,
    token="deleted_user_role_token",
    user_id=deleted_user.id,
    is_client_token=True,
    is_user_token=False,
  )
  deleted_client_role_token = Mock(
    client_id=deleted_client.id,
    token="deleted_client_role_token",
    user_id=user.id,
    is_client_token=True,
    is_user_token=False,
  )
  orphan_user_role_token = Mock(
    client_id=client.id, token="orphan_client_role_token", user_id=next(ids), is_client_token=True, is_user_token=False
  )
  orphan_client_role_token = Mock(
    client_id=next(ids), token="orphan_client_role_token", user_id=user.id, is_client_token=True, is_user_token=False
  )

  @pytest.fixture(
    params=[
      client_token,
      deleted_client_token,
      orphan_client_token,
      role_token,
      deleted_user_role_token,
      deleted_client_role_token,
      orphan_user_role_token,
      orphan_client_role_token,
    ]
  )
  def each_client_token(self, request):
    return request.param

  @pytest.fixture(
    params=[
      user_token,
      deleted_user_token,
      orphan_user_token,
    ]
  )
  def each_user_token(self, request):
    return request.param

  @pytest.fixture(
    params=[
      dict(can_read=True, can_write=False, can_admin=False),
      dict(can_read=True, can_write=True, can_admin=False),
      dict(can_read=True, can_write=True, can_admin=True),
    ]
  )
  def find_role(self, request):
    def dummy_find_role(*pairs):
      def find_function(client_id, user_id):
        for c, u in pairs:
          if (c.id, u.id) == (client_id, user_id):
            return Mock(client_id=client_id, user_id=user_id, **request.param)
        return None

      return find_function

    return dummy_find_role

  @pytest.fixture(params=[mt.value for mt in MembershipType])
  def find_membership(self, request):
    def dummy_find_membership(*pairs):
      def find_function(user_id, organization_id):
        for u, o in pairs:
          if (u.id, o.id) == (user_id, organization_id):
            return Mock(
              spec=Membership,
              user_id=user_id,
              organization_id=organization_id,
              membership_type=request.param,
            )
        return None

      return find_function

    return dummy_find_membership

  @pytest.fixture
  def services(self, find_role, find_membership):
    return Mock(
      client_service=Mock(find_by_id=dummy_find_client_by_id(self.client, self.deleted_client)),
      config_broker=StrictAccessConfigBroker.from_configs({"address": {"app_url": "https://fakeapp.example.com"}}),
      user_service=Mock(find_by_id=dummy_find_user_by_id(self.user, self.deleted_user)),
      membership_service=Mock(
        find_by_user_and_organization=find_membership(
          (self.user, self.organization),
          (self.deleted_user, self.organization),
        )
      ),
      permission_service=Mock(
        find_by_client_and_user=find_role(
          (self.client, self.user),
          (self.deleted_client, self.user),
          (self.client, self.deleted_user),
        )
      ),
      token_service=Mock(
        user_id_from_token=dummy_find_token_by_token_value(
          self.user_token,
          self.deleted_user_token,
          self.orphan_user_token,
        ),
        find_by_token=dummy_find_token_by_token_value(
          self.client_token,
          self.role_token,
          self.deleted_client_token,
          self.deleted_client_role_token,
          self.deleted_user_role_token,
          self.orphan_client_token,
          self.orphan_client_role_token,
          self.orphan_user_role_token,
          self.user_token,
          self.deleted_user_token,
          self.orphan_user_token,
        ),
      ),
    )

  def make_request(self, client_token=None, user_token=None, api_token=None):
    return Mock(
      authorization=Mock(password=Mock(return_value=None)),
      optional_client_token=Mock(return_value=client_token),
      optional_user_token=Mock(return_value=user_token),
      optional_api_token=Mock(return_value=api_token),
      path="",
      headers={},
    )


class TestApiAuth(_TestAuthCore):
  def test_auth_client(self, services):
    request = self.make_request(api_token=self.client_token.token)
    authed = api_token_authentication(services, request)
    assert authed.current_client.id == self.client.id

  def test_auth_user(self, services):
    request = self.make_request(api_token=self.user_token.token)
    authed = api_token_authentication(services, request)
    assert authed.current_user.id == self.user.id

  def test_auth_role(self, services):
    request = self.make_request(api_token=self.role_token.token)
    authed = api_token_authentication(services, request)
    assert authed.current_client.id == self.client.id
    assert authed.current_user.id == self.user.id

  def test_auth_deleted(self, services):
    request = self.make_request(api_token=self.deleted_user_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.deleted_client_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.deleted_user_role_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.deleted_client_role_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

  def test_auth_orphan_token(self, services):
    request = self.make_request(api_token=self.orphan_user_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.orphan_client_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.orphan_user_role_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

    request = self.make_request(api_token=self.orphan_client_role_token.token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

  def test_auth_bad_token(self, services):
    request = self.make_request(api_token=self.bad_token)
    with pytest.raises(ForbiddenError):
      api_token_authentication(services, request)

  def test_auth_no_token(self, services):
    request = self.make_request()
    with pytest.raises(UnauthorizedError):
      api_token_authentication(services, request)


class TestClientAuthorization(_TestAuthCore):
  def test_auth_client(self, services):
    request = self.make_request(client_token=self.client_token.token)
    authed = client_token_authentication(services, request)
    assert authed.current_client.id == self.client.id
    assert authed.current_user is None
    authed = maybe_client_token_authentication(services, request)
    assert authed.current_client.id == self.client.id
    assert authed.current_user is None

  def test_auth_user(self, services, each_user_token):
    request = self.make_request(user_token=each_user_token.token)
    with pytest.raises(UnauthorizedError):
      client_token_authentication(services, request)
    authed = maybe_client_token_authentication(services, request)
    assert authed.current_client is None
    assert authed.current_user is None

  def test_auth_role(self, services):
    request = self.make_request(client_token=self.role_token.token)
    authed = client_token_authentication(services, request)
    assert authed.current_client.id == self.client.id
    assert authed.current_user.id == self.user.id
    authed = maybe_client_token_authentication(services, request)
    assert authed.current_client.id == self.client.id
    assert authed.current_user.id == self.user.id

  def test_auth_deleted_client(self, services):
    request = self.make_request(client_token=self.deleted_client_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_deleted_client_role(self, services):
    request = self.make_request(client_token=self.deleted_client_role_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_deleted_user_role(self, services):
    request = self.make_request(client_token=self.deleted_user_role_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_orphan_token(self, services):
    request = self.make_request(client_token=self.orphan_client_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_orphan_client_role_token(self, services):
    request = self.make_request(client_token=self.orphan_client_role_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_orphan_user_role_token(self, services):
    request = self.make_request(client_token=self.orphan_user_role_token.token)
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)

  def test_auth_bad_token(self, services):
    request = self.make_request(client_token=self.client_token.token + "extra")
    with pytest.raises(ForbiddenError):
      client_token_authentication(services, request)

    with pytest.raises(ForbiddenError):
      maybe_client_token_authentication(services, request)


class TestUserAuthorization(_TestAuthCore):
  def test_auth_client(self, services, each_client_token):
    request = self.make_request(client_token=each_client_token.token)
    with pytest.raises(UnauthorizedError):
      user_token_authentication(services, request)

  def test_auth_user(self, services):
    request = self.make_request(user_token=self.user_token.token)
    authed = user_token_authentication(services, request)
    assert authed.current_user.id == self.user.id

  def test_auth_deleted_user(self, services):
    request = self.make_request(user_token=self.deleted_user_token.token)
    with pytest.raises(ForbiddenError):
      user_token_authentication(services, request)

  def test_auth_orphan_token(self, services):
    request = self.make_request(user_token=self.orphan_user_token.token)
    with pytest.raises(ForbiddenError):
      user_token_authentication(services, request)

  def test_auth_bad_token(self, services):
    request = self.make_request(user_token=self.user_token.token + "extra")
    with pytest.raises(ForbiddenError):
      user_token_authentication(services, request)

  def test_auth_no_token(self, services):
    request = self.make_request(user_token=None)
    with pytest.raises(UnauthorizedError):
      user_token_authentication(services, request)
