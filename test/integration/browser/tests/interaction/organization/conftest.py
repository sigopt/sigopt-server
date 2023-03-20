# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.conftest import log_in_driver


@pytest.fixture
def logged_in_member_driver(_driver, web_connection, member_login_state):
  return log_in_driver(_driver, web_connection, member_login_state)
