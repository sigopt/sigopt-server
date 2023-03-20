# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class TestProject(WebBase):
  @pytest.fixture
  def project(self, api_connection):
    project_id = "project-1"
    return api_connection.clients(api_connection.client_id).projects().create(name=project_id, id=project_id)

  def test_project_does_not_exist(self, web_connection, logged_in_web_connection):
    route = "/project/1234567890"
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)

  def test_project_logged_out(self, web_connection, logged_in_web_connection, project):
    route = f"/project/{project.id}"
    logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)
