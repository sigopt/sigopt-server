# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestSessions(WebBase):
  @pytest.fixture(scope="function")
  def user(self, auth_provider):
    return auth_provider.create_user(
      auth_provider.randomly_generated_email(),
      auth_provider.randomly_generated_password(),
      name="here is an name that is unlikely to occur naturally",
    )

  @pytest.mark.parametrize("store_parent_state", [True, False])
  def test_logged_out_push(self, any_connection, user, store_parent_state):
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.post("/push_session", {"api_token": "invalid-token", "store_parent_state": store_parent_state})

  @pytest.mark.parametrize("store_parent_state", [True, False])
  def test_normal_user_push(self, api_connection, any_connection, user, store_parent_state):
    normal_user_token = api_connection.sessions().fetch().api_token.token
    any_connection.post("/push_session", {"api_token": normal_user_token, "store_parent_state": store_parent_state})
    assert user.email not in any_connection.get("/user/info", raise_for_status=False)

  def test_logged_out_pop(self, web_connection):
    with RaisesHttpError(HTTPStatus.UNAUTHORIZED):
      web_connection.post("/pop_session")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")
