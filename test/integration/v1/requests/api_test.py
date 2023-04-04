# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64
import json
import os
from http import HTTPStatus

import pytest
import requests

from zigopt.common import *

from integration.v1.test_base import V1Base


def request(method, path, **kwargs):
  kwargs.setdefault("verify", os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True))
  return requests.request(method, path, **kwargs)


class TestApiBase(V1Base):
  @pytest.fixture(autouse=True)
  def ensure_api(self, api):
    pass

  @pytest.fixture
  def user_id(self, connection):
    return connection.user_id

  @pytest.fixture
  def auth(self, connection):
    return (connection.user_token, "")

  @pytest.fixture(
    params=[
      {},
      {"Content-Type": "application/json"},
      # curl adds x-www-form-urlencoded by default when using -d.
      # Since this is common for debugging we try to handle this case sensibly
      {"Content-Type": "application/x-www-form-urlencoded"},
    ]
  )
  def headers(self, request):
    return request.param

  def expect_400(self, response):
    assert response.status_code == HTTPStatus.BAD_REQUEST

  def test_invalid_unicode_auth(self, api_url, connection):
    self.expect_400(
      request(
        "GET",
        f"{api_url}/v1/sessions",
        headers={
          "Authorization": "Basic " + base64.b64encode(b"ABCDE\x00:").decode("utf-8"),
        },
      )
    )

  def test_invalid_unicode_path(self, api_url, connection):
    self.expect_400(request("GET", f"{api_url}/v1/\x00"))

  def test_invalid_unicode_body(self, api_url, connection):
    self.expect_400(request("POST", f"{api_url}/v1/verifications", data=json.dumps({"email": "test\x00@sigopt.ninja"})))

  def test_invalid_unicode_param(self, api_url, auth, connection):
    self.expect_400(
      request(
        "GET",
        f"{api_url}/v1/clients/{connection.client_id}/experiments",
        auth=auth,
        params={"search": "experiment\x00"},
      )
    )

  def test_get_json(self, api_url, headers, auth):
    request("GET", api_url + "/v1/sessions", headers=headers, auth=auth).raise_for_status()

  @pytest.mark.parametrize("data", ["", "{}"])
  def test_post_json(self, api_url, headers, data, auth, user_id):
    response = request(
      "POST",
      f"{api_url}/v1/users/{user_id}/verifications",
      headers=headers,
      auth=auth,
      data=data,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.text == "{}\n"

  def test_no_content(self, api_url, headers, auth, user_id):
    response = request(
      "POST",
      f"{api_url}/v1/users/{user_id}/verifications",
      headers=extend_dict({"X-Response-Content": "skip"}, headers),
      auth=auth,
      data="",
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.text == ""

  def test_post_bad_json(self, api_url, headers, auth, user_id):
    response = request(
      "POST",
      f"{api_url}/v1/users/{user_id}/verifications",
      headers=headers,
      auth=auth,
      data="{",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid json" in response.json()["message"]

  def test_post_read_params_json(self, api_url, headers, auth):
    response = request(
      "POST",
      api_url + "/v1/verifications",
      headers=headers,
      auth=auth,
      data='{"email":"someuser@sigopt.ninja"}',
    )
    assert response.status_code == HTTPStatus.OK
