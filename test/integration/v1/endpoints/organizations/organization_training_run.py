# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
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


class TestOrganizationTrainingRun(V1Base):
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
    message = response.json().get("message")
    assert "Invalid string parameter" in message or message == "Bad Request"

  def test_make_basic_filter_request(
    self,
    api_url,
    auth,
    connection,
    services,
    project,
    aiexperiment_in_project,
    owner_connection_same_organization,
  ):
    self.throw_down_a_bunch_of_training_runs_(
      connection, services, project, aiexperiment_in_project, owner_connection_same_organization
    )
    response = request(
      "GET",
      f"{api_url}/v1/organizations/{connection.organization_id}/training_runs",
      auth=auth,
      params={"filters": json.dumps([{"field": "experiment", "operator": "==", "value": aiexperiment_in_project.id}])},
    )
    resp_obj = json.loads(response.text)
    assert resp_obj["count"] == 6

  def test_make_optimized_filter_request(
    self,
    api_url,
    auth,
    connection,
    services,
    project,
    aiexperiment_in_project,
    owner_connection_same_organization,
  ):
    self.throw_down_a_bunch_of_training_runs_(
      connection, services, project, aiexperiment_in_project, owner_connection_same_organization
    )
    response = request(
      "GET",
      f"{api_url}/v1/organizations/{connection.organization_id}/training_runs",
      auth=auth,
      params={"filters": json.dumps([{"field": "optimized_suggestion", "operator": "==", "value": True}])},
    )
    resp_obj = json.loads(response.text)
    assert resp_obj["count"] == 5
    response = request(
      "GET",
      f"{api_url}/v1/organizations/{connection.organization_id}/training_runs",
      auth=auth,
      params={"filters": json.dumps([{"field": "optimized_suggestion", "operator": "==", "value": False}])},
    )
    resp_obj = json.loads(response.text)
    assert resp_obj["count"] == 1

  def throw_down_a_bunch_of_training_runs_(
    self, connection, services, project, aiexperiment_in_project, owner_connection_same_organization
  ):
    for name in [
      "runBeforeStartOrg",
      "runFirstOrg",
      "runSecondOrg",
    ]:
      connection.aiexperiments(aiexperiment_in_project.id).training_runs().create(
        name=name,
      )

    connection.aiexperiments(aiexperiment_in_project.id).training_runs().create(
      name="runUserCreatedOrg",
      assignments={"x": 1.5, "y": 2},
    )

    owner_connection_same_organization.aiexperiments(aiexperiment_in_project.id).training_runs().create(
      name="runOtherUserOrg",
    )

    connection.aiexperiments(aiexperiment_in_project.id).training_runs().create(
      name="runAfterStopOrg",
    )
