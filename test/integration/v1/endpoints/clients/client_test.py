# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.membership.model import MembershipType

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestClients(V1Base):
  @pytest.fixture(params=["prod", "dev"])
  def this_connection(self, request, connection, development_connection):
    if request.param == "dev":
      return development_connection
    return connection

  def test_detail_client(self, this_connection):
    client_detail = this_connection.clients(this_connection.client_id).fetch()
    assert client_detail is not None
    assert int(this_connection.client_id) == int(client_detail.id)
    assert int(this_connection.organization_id) == int(client_detail.organization)

  def test_experiments(self, this_connection):
    e = this_connection.create_any_experiment()
    client_experiments = this_connection.clients(this_connection.client_id).experiments().fetch().data
    assert len(client_experiments) == 1
    assert client_experiments[0].id == e.id


class TestClientCreate(V1Base):
  def test_create_client(self, connection, services):
    client_name = "zzzzzz"
    client = connection.clients().create(name=client_name)
    assert client.name == client_name
    assert client.created is not None
    assert client.to_json()["client_security"]["allow_users_to_see_experiments_by_others"] is True
    user_permissions = connection.users(connection.user_id).permissions().fetch()
    assert client.id in [r.client.id for r in user_permissions.iterate_pages()]

    client_permissions = connection.clients(client.id).permissions().fetch()
    assert client_permissions.count == 1
    assert client_permissions.data[0].user.id == connection.user_id
    assert client_permissions.data[0].to_json()["can_see_experiments_by_others"] is True

    client_obj = services.client_service.find_by_id(int(client.id))
    organization_obj = services.organization_service.find_by_id(client_obj.organization_id)
    assert organization_obj.name == client_name

    membership_obj = services.membership_service.find_by_user_and_organization(
      user_id=int(connection.user_id), organization_id=organization_obj.id
    )
    assert membership_obj is not None
    assert membership_obj.user_id == int(connection.user_id)
    assert membership_obj.organization_id == organization_obj.id
    assert membership_obj.membership_type == MembershipType.owner

    example_project = connection.clients(client.id).projects("sigopt-examples").fetch()
    assert example_project.id == "sigopt-examples"
    assert example_project.client == client.id

  def test_create_private_client(self, connection):
    client_name = "yyyyyy"
    client = connection.clients().create(
      name=client_name, client_security={"allow_users_to_see_experiments_by_others": False}
    )
    assert client.name == client_name
    assert client.created is not None
    # TODO: Change when the python API client gets changed
    assert client.to_json()["client_security"]["allow_users_to_see_experiments_by_others"] is False

  def test_admin_in_private_client(self, connection, config_broker, auth_provider, inbox):
    client = connection.clients().create(
      name="xxxxxx", client_security={"allow_users_to_see_experiments_by_others": False}
    )
    new_user_email = auth_provider.randomly_generated_email()
    auth_provider.create_user_tokens(email=new_user_email, has_verified_email=True)
    connection.clients(client.id).invites().create(email=new_user_email, role=ADMIN_ROLE, old_role=NO_ROLE)
    permissions = connection.clients(client.id).permissions().fetch().data
    assert len(permissions) == 2
    assert permissions[0].to_json()["can_see_experiments_by_others"] is True
    assert permissions[1].to_json()["can_see_experiments_by_others"] is True

  def test_write_in_private_client(self, connection, config_broker, auth_provider, inbox):
    client = connection.clients().create(
      name="wwwwww", client_security={"allow_users_to_see_experiments_by_others": False}
    )
    new_user_email = auth_provider.randomly_generated_email()
    auth_provider.create_user_tokens(email=new_user_email, has_verified_email=True)
    connection.clients(client.id).invites().create(email=new_user_email, role=USER_ROLE, old_role=NO_ROLE)
    permissions = connection.clients(client.id).permissions().fetch().data
    assert len(permissions) == 2
    assert permissions[0].to_json()["can_see_experiments_by_others"] is True
    assert permissions[1].to_json()["can_see_experiments_by_others"] is False

  def test_read_in_private_client(self, connection, config_broker, auth_provider, inbox):
    client = connection.clients().create(
      name="vvvvvvv", client_security={"allow_users_to_see_experiments_by_others": False}
    )
    new_user_email = auth_provider.randomly_generated_email()
    auth_provider.create_user_tokens(email=new_user_email, has_verified_email=True)
    connection.clients(client.id).invites().create(email=new_user_email, role=READ_ONLY_ROLE, old_role=NO_ROLE)
    permissions = connection.clients(client.id).permissions().fetch().data
    assert len(permissions) == 2
    assert permissions[0].to_json()["can_see_experiments_by_others"] is True
    assert permissions[1].to_json()["can_see_experiments_by_others"] is False


class TestClientDelete(V1Base):
  def test_delete_client(self, connection, services):
    client = connection.clients().create(name="test name")
    connection.clients(client.id).delete()

    # Since client will be only one in its org, delete should delete the org
    client_obj = services.client_service.find_by_id(client.id, include_deleted=True)
    organization_obj = services.organization_service.find_by_id(client_obj.organization_id, include_deleted=True)
    assert organization_obj.deleted is True

    # Since we don't surface client soft-deletes to non-admin we should throw 404
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(client.id).fetch()


class TestClientUpdate(V1Base):
  def test_update_name(self, connection):
    client = connection.clients(connection.client_id).fetch()
    updated_response = connection.clients(client.id).update(name="new name")
    assert updated_response.name == "new name"
    updated_client = connection.clients(client.id).fetch()
    assert updated_client.name == "new name"

  def test_update_privacy(self, connection):
    client = connection.clients(connection.client_id).fetch()
    assert client.to_json()["client_security"]["allow_users_to_see_experiments_by_others"] is True

    updated_response = connection.clients(client.id).update(
      client_security={"allow_users_to_see_experiments_by_others": False}
    )
    assert updated_response.to_json()["client_security"]["allow_users_to_see_experiments_by_others"] is False

    updated_client = connection.clients(client.id).fetch()
    assert updated_client.to_json()["client_security"]["allow_users_to_see_experiments_by_others"] is False

  def test_update_permissions_privacy_read(self, connection, read_connection_same_client):
    client = connection.clients(connection.client_id).fetch()
    permissions = connection.clients(client.id).permissions().fetch().data

    assert len(permissions) == 2
    assert permissions[0].to_json()["can_see_experiments_by_others"] is True
    assert permissions[1].to_json()["can_see_experiments_by_others"] is True

    connection.clients(client.id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    # Get updated permissions
    permissions = connection.clients(client.id).permissions().fetch().data

    assert len(permissions) == 2
    admin_permission = next(p for p in permissions if p.user.id == connection.user_id)
    read_permission = next(p for p in permissions if p.user.id == read_connection_same_client.user_id)

    # Admin's value remains True
    assert admin_permission.to_json()["can_see_experiments_by_others"] is True
    assert read_permission.to_json()["can_see_experiments_by_others"] is False

  def test_update_permissions_privacy_write(self, connection, write_connection_same_client):
    client = connection.clients(connection.client_id).fetch()
    permissions = connection.clients(client.id).permissions().fetch().data

    assert len(permissions) == 2
    assert permissions[0].to_json()["can_see_experiments_by_others"] is True
    assert permissions[1].to_json()["can_see_experiments_by_others"] is True

    connection.clients(client.id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    # Get updated permissions
    permissions = connection.clients(client.id).permissions().fetch().data

    assert len(permissions) == 2
    admin_permission = next(p for p in permissions if p.user.id == connection.user_id)
    write_permission = next(p for p in permissions if p.user.id == write_connection_same_client.user_id)
    # Admin's value remains True
    assert admin_permission.to_json()["can_see_experiments_by_others"] is True
    assert write_permission.to_json()["can_see_experiments_by_others"] is False

  def test_write_user_cant_update(self, read_connection):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection.clients(read_connection.client_id).update(name="New name")
