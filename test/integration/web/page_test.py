# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
from http import HTTPStatus

import pytest
import requests

from integration.base import RaisesHttpError
from integration.web.test_base import Routes, WebBase


class TestPages(WebBase):
  @pytest.fixture(params=[p for p in Routes.ALL_ROUTES if p.startswith("/experiment/:experimentId")])
  def test_experiment_urls(self, api_connection, logged_in_web_connection, request):
    url = request.param
    e = api_connection.create_any_experiment()
    logged_in_web_connection.get(url.replace(":experimentId", e.id))

  @pytest.fixture(params=[p for p in Routes.ALL_ROUTES if p.startswith("/experiment/:experimentId")])
  def test_experiment_urls_invalid_id(self, api_connection, logged_in_web_connection, request):
    url = request.param
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(url.replace(":experimentId", "notanid"))

  def test_health(self, config_broker, web):
    del web
    app_url = self.get_app_url(config_broker)
    response = requests.get(f"{app_url}/nhealth", verify=os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True), timeout=5)
    assert response.status_code == 200
    assert response.text.strip() == "healthy"

  @pytest.mark.parametrize(
    "url",
    [
      "/",
      "/login",
      "/signup?code=x",
    ],
  )
  def test_common_pages(self, any_connection, url):
    assert any_connection.get(url)

  def test_404(self, any_connection):
    # Ensure file uploads aren't read except on explicitly allowed pages
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.get("/fakeurl")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.get("/static/fakeasset")

  def test_file_upload_wrong_page(self, any_connection):
    # Ensure file uploads aren't read except on explicitly allowed pages
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      any_connection.post_file("/fakeurl", data="abcde", filename="bulk-file")
