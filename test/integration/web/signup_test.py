# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.web.test_base import WebBase


class TestSignup(WebBase):
  @pytest.fixture(autouse=True)
  def signup_enabled(self, config_broker):
    if config_broker.get("features.requireInvite"):
      pytest.skip()

  def test_logged_in_get(self, logged_in_web_connection):
    response = logged_in_web_connection.get("/signup", allow_redirects=True)
    assert response.response.url.endswith("/home")
