# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestUserDelete(V1Base):
  def test_delete(self, owner_connection, config_broker):
    owner_connection.clients(owner_connection.client_id).delete()
    owner_connection.users(owner_connection.user_id).delete(password=owner_connection.password)

  def test_delete_no_password(self, owner_connection, config_broker):
    owner_connection.clients(owner_connection.client_id).delete()
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection.users(owner_connection.user_id).delete()

  def test_delete_wrong_password(self, owner_connection, config_broker):
    owner_connection.clients(owner_connection.client_id).delete()
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection.users(owner_connection.user_id).delete(password="zzzzzzz")

  # TODO: need to make sure organization owners cant delete themselves
  @pytest.mark.xfail
  def test_owner_needs_client_delete(self, owner_connection, config_broker):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      owner_connection.users(owner_connection.user_id).delete(password=owner_connection.password)

  def test_needs_client_delete(self, connection, config_broker):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.users(connection.user_id).delete(password=connection.password)
