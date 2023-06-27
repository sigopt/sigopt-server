# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import io
from http import HTTPStatus

import pytest

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestCsrf(WebBase):
  def check_csrf(self, any_connection, url, files=None):
    with RaisesHttpError(HTTPStatus.BAD_REQUEST) as e:
      any_connection.post(url, hide_csrf=True, files=files)
    assert "Missing csrf" in e.value.response.text

  def test_csrf(self, api_connection, any_connection):
    any_connection.get("/")
    self.check_csrf(any_connection, "/login")
    self.check_csrf(any_connection, "/change_password")
    self.check_csrf(any_connection, "/signup")
    self.check_csrf(any_connection, "/push_session")
    self.check_csrf(any_connection, "/pop_session")

  @pytest.mark.parametrize(
    "url",
    [
      "/client/{client_id}/delete",
      "/clients/create",
      "/experiment/{experiment_id}/report",
      "/experiment/{experiment_id}/reset",
      "/push_session",
      "/user/i_want_to_delete_my_account",
    ],
  )
  def test_csrf_logged_in(self, api_connection, logged_in_web_connection, url):
    e = api_connection.create_any_experiment()
    self.check_csrf(
      logged_in_web_connection,
      url.format(
        client_id=api_connection.client_id,
        experiment_id=e.id,
      ),
    )

  def test_csrf_logged_in_file(self, api_connection, logged_in_web_connection):
    e = api_connection.create_any_experiment()
    self.check_csrf(
      logged_in_web_connection,
      f"/experiment/{e.id}/report/file",
      files={
        "bulk-file": io.StringIO(""),
      },
    )

  def test_bad_urls(self, any_connection):
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.post("/fakeurl", hide_csrf=True)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.post("/fakeurl", hide_csrf=False)
