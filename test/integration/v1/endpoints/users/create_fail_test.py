# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestUserCreateFail(V1Base):
  def test_create_forbidden(self, anonymous_connection, inbox, config_broker):
    if not config_broker.get("features.requireInvite"):
      pytest.skip()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      anonymous_connection.users().create(
        name="Some user",
        email=AuthProvider.randomly_generated_email(),
        password=AuthProvider.randomly_generated_password(),
        client_name="client name",
      )
