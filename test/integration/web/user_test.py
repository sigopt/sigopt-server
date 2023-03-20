# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestUserProfile(WebBase):
  def test_user_logged_out(self, web_connection, logged_in_web_connection):
    route = "/user/info"
    logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)
