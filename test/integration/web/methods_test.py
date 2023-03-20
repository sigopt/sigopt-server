# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
from http import HTTPStatus

import pytest
import requests

from integration.web.test_base import WebBase


ALLOWED_METHODS = [
  ("DELETE", "/v1/experiments/0"),
  ("GET", ""),
  ("MERGE", "/v1/training_runs/0"),
  ("OPTIONS", ""),
  ("POST", "/v1/clients/0/experiments"),
  ("PUT", "/v1/experiments/0"),
]

BLOCKED_METHODS = [
  "CONNECT",
  "CoNnEcT",
  "aksjdoij",
]

assert not (set(m for m, _ in ALLOWED_METHODS) & set(BLOCKED_METHODS))


def request(method, path):
  return requests.request(method, path, verify=os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True))


class TestHTTPMethods(WebBase):
  """Check that known request methods are allowed by NGINX and that unknown method are blocked."""

  @pytest.mark.parametrize("method,path", ALLOWED_METHODS)
  def test_allowed_api_method(self, api_url, method, path):
    response = request(method, f"{api_url}{path}")
    assert response.status_code != HTTPStatus.METHOD_NOT_ALLOWED, response.content.decode("utf-8")

  @pytest.mark.parametrize("method,path", ALLOWED_METHODS)
  def test_allowed_web_method(self, app_url, method, path):
    response = request(method, f"{app_url}/api{path}")
    assert response.status_code != HTTPStatus.METHOD_NOT_ALLOWED, response.content.decode("utf-8")

  @pytest.mark.parametrize("method", BLOCKED_METHODS)
  def test_unknown_api_method_blocked(self, api_url, method):
    response = request(method, api_url)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, response.content.decode("utf-8")

  @pytest.mark.parametrize("method", BLOCKED_METHODS)
  def test_unknown_web_method_blocked(self, app_url, method):
    response = request(method, f"{app_url}/api/")
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, response.content.decode("utf-8")
