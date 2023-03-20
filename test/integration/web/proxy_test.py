# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
from http import HTTPStatus

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestProxy(WebBase):
  def test_invalid_endpoint(self, any_connection):
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.get("/api/blahblah")

  def test_valid_endpoint(self, logged_in_web_connection, api_connection, login_state):
    proxy_response = logged_in_web_connection.get(
      f"/api/v1/users/{login_state.user_id}",
      auth=(login_state.client_token, ""),
    )
    proxy_json = json.loads(proxy_response.response_text())

    api_json = api_connection.users(login_state.user_id).fetch().to_json()
    assert proxy_json == api_json

  def test_no_authentication(self, any_connection, login_state):
    with RaisesHttpError(HTTPStatus.UNAUTHORIZED):
      assert any_connection.get(f"/api/v1/users/{login_state.user_id}")
