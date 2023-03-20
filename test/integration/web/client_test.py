# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestClientSwitch(WebBase):
  @pytest.fixture(scope="function")
  def credentials(self, login_state):
    return login_state.email, login_state.password

  def test_client_does_not_exist(self, web_connection, logged_in_web_connection):
    route = "/client/1234567890/tokens"
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)

  def test_client_logged_out(self, api_connection, web_connection, logged_in_web_connection):
    route = f"/client/{api_connection.client_id}/tokens"
    logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)

  def test_client_switch(self, api_connection, logged_in_web_connection, credentials):
    user_id = api_connection.sessions().fetch().user.id
    other_client = api_connection.clients().create(name="abc")
    other_tokens = [
      t for t in api_connection.clients(other_client.id).tokens().fetch().iterate_pages() if t.user == user_id
    ]
    assert len(other_tokens) == 2
    other_token = find(other_tokens, lambda t: not t.development)
    other_token = other_token.token

    tokens_page = logged_in_web_connection.get("/tokens/info")
    assert other_token not in tokens_page

    logged_in_web_connection.post(
      "/push_session",
      {
        "api_token": other_token,
        "client_id": other_client.id,
      },
    )

    logged_in_web_connection.post("/logout")
    email, password = credentials
    logged_in_web_connection.post("/login", {"email": email, "password": password})

    tokens_page = logged_in_web_connection.get("/tokens/info")
    assert other_token in tokens_page
