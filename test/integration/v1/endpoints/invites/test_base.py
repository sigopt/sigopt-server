# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.v1.test_base import V1Base


class InviteTestBase(V1Base):
  @pytest.fixture
  def owner(self, connection):
    return connection.sessions().fetch().user

  @classmethod
  @pytest.fixture
  def invitee_connection(cls, config_broker, api, auth_provider, api_url):
    return cls.make_v1_connection(config_broker, api, auth_provider, has_verified_email=False)

  @pytest.fixture
  def invitee(self, invitee_connection):
    return invitee_connection.connection.sessions().fetch().user

  @classmethod
  @pytest.fixture
  def second_invitee_connection(cls, config_broker, api, auth_provider, api_url):
    return cls.make_v1_connection(config_broker, api, auth_provider, has_verified_email=False)

  @pytest.fixture
  def second_invitee(self, second_invitee_connection):
    return second_invitee_connection.connection.sessions().fetch().user

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def organization_id(self, connection):
    return connection.organization_id
