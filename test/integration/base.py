# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest
import requests
from sigopt.exception import ApiException


class RaisesHttpError(object):
  def __init__(self, *status_codes):
    for code in status_codes:
      assert isinstance(code, HTTPStatus)
    self.underlying = pytest.raises(requests.HTTPError)
    self.status_codes = status_codes

  def __enter__(self):
    return self.underlying.__enter__()

  def __exit__(self, exc_type, exc_value, tb):
    ret = self.underlying.__exit__(exc_type, exc_value, tb)
    if isinstance(exc_value, requests.HTTPError):
      if exc_value.response.status_code not in self.status_codes:
        print(exc_value)  # noqa: T001
        return False
    return ret


class RaisesApiException(object):
  def __init__(self, *status_codes):
    for code in status_codes:
      assert isinstance(code, HTTPStatus)
    self.underlying = pytest.raises(ApiException)
    self.status_codes = status_codes

  def __enter__(self):
    return self.underlying.__enter__()

  def __exit__(self, exc_type, exc_value, tb):
    ret = self.underlying.__exit__(exc_type, exc_value, tb)
    if isinstance(exc_value, ApiException):
      if exc_value.status_code not in self.status_codes:
        print(exc_value)  # noqa: T001
        return False
    return ret


class BaseTest(object):
  @classmethod
  def get_api_url(cls, config_broker):
    return config_broker["address.api_url"]

  @classmethod
  def get_app_url(cls, config_broker):
    return config_broker["address.app_url"]
