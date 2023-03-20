# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


# customlint: disable=AccidentalFormatStringRule
class TestOrganizations(WebBase):
  @pytest.fixture
  def organization_id(self, login_state):
    return login_state.organization_id

  @pytest.fixture
  def organization_name(self, organization_id, api_connection):
    return api_connection.organizations(organization_id).fetch().name

  @pytest.mark.parametrize(
    "from_url,to_url",
    [
      ["/organization", "/organization/users"],
      ["/organization/experiments", "/organization/{organization_id}/experiments"],
      ["/organization/teams", "/organization/{organization_id}/teams"],
      ["/organization/users", "/organization/{organization_id}/users"],
    ],
  )
  def test_organization_redirects(self, logged_in_web_connection, organization_id, to_url, from_url):
    to_url = to_url.format(organization_id=organization_id)
    assert logged_in_web_connection.get(from_url, allow_redirects=False).redirect_url.endswith(to_url)

  def test_organization_page(self, logged_in_web_connection, organization_id, auth_provider, organization_name):
    other_organization_id = self.make_login_state(auth_provider)
    assert organization_name in logged_in_web_connection.get(f"/organization/{organization_id}/experiments")
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(f"/organization/{other_organization_id}/experiments")

  def test_organization_does_not_exist(self, web_connection, logged_in_web_connection):
    route = "/organization/1234567890"
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)

  def test_organization_logged_out(self, web_connection, logged_in_web_connection, organization_id):
    route_with_id = f"/organization/{organization_id}/experiments"
    route_without_id = "/organization/experiments"
    logged_in_web_connection.get(route_with_id)
    logged_in_web_connection.get(route_without_id)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route_with_id)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route_without_id)

  @pytest.mark.parametrize(
    "url",
    [
      "/organization/{organization_id}/teams",
      "/organization/{organization_id}/users",
      "/organization/{organization_id}",
    ],
  )
  def test_empty_organization(self, login_state, logged_in_web_connection, url):
    logged_in_web_connection.get(url.format(organization_id=login_state.organization_id))
