# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestLogin(WebBase):
  @pytest.fixture(scope="function")
  def credentials(self, login_state):
    return login_state.email, login_state.password

  def test_login(self, web_connection, credentials):
    email, password = credentials
    web_connection.post("/login", {"email": email, "password": password})
    assert web_connection.get("/user/info", allow_redirects=False).redirect_url is None

  def test_continue(self, config_broker, web_connection, credentials):
    email, password = credentials
    continue_url = self.get_app_url(config_broker) + "/experiments/create"
    assert "Create Experiment" in web_connection.post(
      "/login",
      {
        "email": email,
        "password": password,
        "continue": continue_url,
      },
    )

  def test_external_continue(self, config_broker, web_connection, credentials):
    email, password = credentials
    continue_url = self.get_api_url(config_broker)
    response = web_connection.post(
      "/login",
      {
        "email": email,
        "password": password,
        "continue": continue_url,
      },
      allow_redirects=False,
    ).response
    assert response.headers["Location"] == continue_url

  def test_no_params(self, web_connection):
    web_connection.post("/login")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")

  def test_no_email(self, web_connection):
    with RaisesHttpError(HTTPStatus.BAD_REQUEST):
      web_connection.post("/login", {"password": "somerandompassword"})
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")

  def test_no_password(self, web_connection, credentials):
    email, _ = credentials
    with RaisesHttpError(HTTPStatus.BAD_REQUEST):
      web_connection.post("/login", {"email": email})
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")

  def test_wrong_password(self, web_connection, credentials):
    email, _ = credentials
    with RaisesHttpError(HTTPStatus.BAD_REQUEST):
      web_connection.post("/login", {"email": email, "password": "wrongpassword"})
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")


class TestProfile(WebBase):
  def test_profile(self, logged_in_web_connection):
    assert "My Organizations" in logged_in_web_connection.get("/user/info")


class TestAlreadyLoggedIn(WebBase):
  @pytest.fixture(scope="function")
  def credentials(self, login_state):
    return login_state.email, login_state.password

  def test_logged_in_get(self, config_broker, logged_in_web_connection):
    response = logged_in_web_connection.get("/login", allow_redirects=False)
    assert response.redirect_url.endswith("/home")

  def test_logged_in_get_continue(self, config_broker, logged_in_web_connection):
    continue_url = self.get_app_url(config_broker) + "/experiments/create"
    response = logged_in_web_connection.get(f"/login?continue={continue_url}", allow_redirects=False)
    assert response.redirect_url.endswith(continue_url)

  def test_logged_in_post(self, credentials, logged_in_web_connection):
    email, password = credentials
    response = logged_in_web_connection.post(
      "/login",
      {
        "email": email,
        "password": password,
      },
      allow_redirects=False,
    )
    assert response.redirect_url.endswith("/home")

  def test_logged_in_post_continue(self, config_broker, credentials, logged_in_web_connection):
    continue_url = self.get_app_url(config_broker) + "/experiments/create"
    email, password = credentials
    response = logged_in_web_connection.post(
      "/login",
      {
        "email": email,
        "password": password,
        "continue": continue_url,
      },
      allow_redirects=False,
    )
    assert response.redirect_url.endswith(continue_url)


class TestLogOut(WebBase):
  def test_log_out(self, config_broker, logged_in_web_connection):
    logged_in_web_connection.get("/user/info")
    response = logged_in_web_connection.post("/logout", allow_redirects=False, data={"continue": "/fake/continue"})
    assert response.redirect_url.endswith("/fake/continue")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get("/user/info")

  def test_session_becomes_invalid(self, config_broker, web_connection, logged_in_web_connection):
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")
    web_connection.copy_cookies_from(logged_in_web_connection.cookies)
    web_connection.get("/user/info")
    logged_in_web_connection.post("/logout")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/user/info")
