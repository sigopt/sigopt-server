# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
from http import HTTPStatus

import pytest
import requests

from integration.v1.test_base import V1Base


def request(method, path, timeout=1, **kwargs):
  kwargs.setdefault("verify", os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True))
  return requests.request(method, path, timeout=timeout, **kwargs)


class TestRequestParsing(V1Base):
  @pytest.fixture(autouse=True)
  def requires_api(self, api):
    pass

  def test_json_integer_dos_not_found(self, api_url):
    response = request("POST", f"{api_url}/", data="9" * 2000000)
    assert response.status_code == HTTPStatus.NOT_FOUND

  def test_json_integer_dos_bad_request(self, api_url):
    response = request("POST", f"{api_url}/v1/clients", data="9" * 2000000)
    assert response.status_code == HTTPStatus.BAD_REQUEST

  @pytest.mark.parametrize("invalid_float", ["inf", "nan"])
  def test_json_float_bad_request(self, api_url, invalid_float):
    response = request("POST", f"{api_url}/v1/clients", data=f'{{"name": {invalid_float}}}')
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["message"].startswith("Malformed json in request body")
