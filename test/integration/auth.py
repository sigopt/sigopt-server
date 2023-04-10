# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigopt.objects import User as JsonUser

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.json.builder import UserJsonBuilder
from zigopt.membership.model import Membership, MembershipType
from zigopt.organization.model import Organization
from zigopt.permission.model import Permission
from zigopt.project.service import create_example_project
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.organization.organizationmeta_pb2 import OrganizationMeta
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, NONE, READ, WRITE, TokenMeta
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta
from zigopt.token.model import Token
from zigopt.token.token_types import TokenType
from zigopt.user.model import User, password_hash

from integration.utils.random_email import generate_random_email


def token_value(seed_value, name):
  return random_string() if seed_value is None else hex(hash((seed_value, name)))[2:]


class AuthProvider:
  def __init__(self, config_broker, db_connection, api_url, services):
    self.api_url = api_url
    self.config_broker = config_broker
    self.db_connection = db_connection
    self.services = services

  def create_client_tokens(
    self,
    permission=ADMIN,
    membership_type=MembershipType.member,
    user_id=None,
    development=False,
  ):
    organization_obj = self._create_organization_object()
    client_obj = self._create_client_object(organization_obj.id)
    client_id = str(client_obj.id)
    organization_id = str(organization_obj.id)
    client_token = self.create_client_token(client_id, user_id, development=development)
    if user_id:
      self.create_membership(
        user_id=user_id,
        organization_id=organization_obj.id,
        membership_type=membership_type,
      )
      if membership_type != MembershipType.owner:
        self.create_permission(
          user_id=user_id,
          client_id=client_id,
          permission=permission,
        )
    return client_id, client_token, organization_id

  def create_user_tokens(
    self,
    email=None,
    password=None,
    edu=False,
    has_verified_email=False,
  ):
    email = email or self.randomly_generated_email()
    password = password or self.randomly_generated_password()
    user = self.create_user(
      email=email,
      password=password,
      edu=edu,
      has_verified_email=has_verified_email,
    )
    user_id = user.id
    user_token = self.create_user_token(user_id)
    return user_id, user_token

  def _create_organization_object(self):
    organization_meta = OrganizationMeta()
    organization = Organization(
      name=f"</script>Integration Test Organization {random_string(10)}",
      organization_meta=organization_meta,
    )
    self.db_connection.insert(organization)
    return organization

  def _create_client_object(self, organization_id):
    client = Client(
      organization_id=organization_id,
      name=f"</script>Integration Test Client {random_string(10)}",
      client_meta=ClientMeta(),
    )
    self.db_connection.insert(client)
    self.db_connection.insert(create_example_project(client_id=client.id))
    return client

  def create_client_token(self, client_id, user_id, seed_value=None, development=False):
    client_token = Token(
      client_id=client_id,
      user_id=user_id,
      token_type=(TokenType.CLIENT_DEV if development else TokenType.CLIENT_API),
      token=token_value(seed_value, "client"),
      meta=TokenMeta(guest_permissions=WRITE),
    )
    self.db_connection.insert(client_token)
    return client_token.token

  def create_user(
    self,
    email=None,
    password=None,
    name=None,
    has_verified_email=False,
    edu=False,
  ):
    email = email or self.randomly_generated_email()
    password = password or self.randomly_generated_password()
    user_meta = UserMeta()
    user_meta.has_verified_email = has_verified_email
    user_meta.educational_user = edu
    user = User(
      email=email or self.randomly_generated_email(),
      hashed_password=password_hash(
        password or self.randomly_generated_password(),
        work_factor=self.config_broker.get("user.password_work_factor"),
      ),
      name=name or f"</script>Integration Test User {random_string(10)}",
      user_meta=user_meta,
    )
    self.db_connection.insert(user)
    return JsonUser(UserJsonBuilder.json(user))

  def create_user_token(self, user_id, seed_value=None):
    user_token = Token(
      user_id=user_id,
      client_id=None,
      token_type=TokenType.USER,
      token=token_value(seed_value, "user"),
      meta=TokenMeta(
        date_created=unix_timestamp(),
        can_renew=True,
        ttl_seconds=14 * 24 * 60 * 60,
      ),
    )
    self.db_connection.insert(user_token)
    return user_token.token

  def create_membership(self, user_id, organization_id, membership_type=MembershipType.member):
    membership = Membership(
      user_id=user_id,
      organization_id=organization_id,
      membership_type=membership_type,
    )
    self.db_connection.insert(membership)
    return membership

  def create_permission(self, user_id, client_id, permission):
    if permission == READ:
      p_list = [True, False, False]
    elif permission == WRITE:
      p_list = [True, True, False]
    elif permission == ADMIN:
      p_list = [True, True, True]
    else:
      assert permission == NONE
      p_list = [False, False, False]
    client = self.db_connection.one(self.db_connection.query(Client).filter_by(id=client_id))
    self.db_connection.insert(
      Permission(
        client_id=client.id,
        user_id=user_id,
        organization_id=client.organization_id,
        permission_meta=PermissionMeta(
          can_read=p_list[0],
          can_write=p_list[1],
          can_admin=p_list[2],
        ),
      )
    )

  @classmethod
  def randomly_generated_email(cls):
    return generate_random_email()

  @classmethod
  def randomly_generated_password(cls):
    return random_string(24) + "aA9!"
