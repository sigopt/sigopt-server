# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import random_string
from zigopt.membership.model import MembershipType
from zigopt.organization.model import Organization
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta
from zigopt.user.model import User

from integration.base import BaseTest
from integration.utils.random_email import generate_random_email


class ServiceBase(BaseTest):
  @pytest.fixture
  def normal_user(self, services):
    return self.make_user(services, "Normal User")

  @pytest.fixture(scope="function")
  def organization(self, services):
    return self.make_organization(services, "Test Organization 1")

  @pytest.fixture(scope="function")
  def other_organization(self, services):
    return self.make_organization(services, "Test Organization 2")

  @pytest.fixture(scope="function")
  def client(self, services, organization):
    return self.make_client(services, "Test Client 1", organization)

  @pytest.fixture(scope="function")
  def other_client(self, services, other_organization):
    return self.make_client(services, "Test Client 2", other_organization)

  def make_user(self, services, name):
    user_meta = UserMeta()
    user_meta.has_verified_email = True
    user = User(name=name, email=generate_random_email(), user_meta=user_meta)
    services.user_service.insert(user)
    return user

  @classmethod
  def make_organization(cls, services, name):
    organization = Organization(name=name)
    return services.organization_service.insert(organization)

  @classmethod
  def make_client(cls, services, name, organization, client_meta=None):
    if not client_meta:
      client_meta = ClientMeta()
      client_meta.date_created = unix_timestamp()
    client = Client(
      name=name,
      client_meta=client_meta,
      organization_id=organization.id,
    )
    return services.client_service.insert(client)

  @classmethod
  def make_membership(cls, services, user, organization, is_owner=False):
    membership_type = MembershipType.owner if is_owner else MembershipType.member
    return services.membership_service.insert(
      user_id=user.id,
      organization_id=organization.id,
      membership_type=membership_type,
    )

  @classmethod
  def make_permission(cls, services, user, client, role):
    return services.permission_service.upsert_from_role(
      role,
      client,
      user,
      requestor=user,
    )

  @classmethod
  def make_invite(
    cls,
    services,
    email,
    organization,
    inviter,
    membership_type=MembershipType.member,
  ):
    invite = services.invite_service.create_invite(
      email,
      organization.id,
      inviter.id,
      random_string(),
      membership_type,
    )
    services.invite_service.insert_invite(invite)
    return invite

  @classmethod
  def make_pending_permission(cls, services, invite, client, role):
    pending_permission = services.pending_permission_service.create_pending_permission(invite, client, role)
    return services.pending_permission_service.insert(pending_permission)
