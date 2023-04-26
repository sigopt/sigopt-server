# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest
import requests
from flaky import flaky

from zigopt.common import *
from zigopt.protobuf.lib import copy_protobuf
from zigopt.token.model import Token

from integration.base import RaisesHttpError
from integration.web.test_base import WebBase


class GuestWebTestBase(WebBase):
  @pytest.fixture
  def experiment(self, api_connection):
    project = api_connection.clients(api_connection.client_id).projects().create(id="my-project", name="Project")
    return api_connection.create_any_experiment(project=project.id)

  @pytest.fixture
  def experiment_guest_token(self, experiment, api_connection):
    return api_connection.experiments(experiment.id).tokens().create().token

  @pytest.fixture
  def experiment_guest_url(self, experiment_guest_token):
    return "/guest?guest_token=" + experiment_guest_token

  @pytest.fixture
  def training_run(self, api_connection):
    project = api_connection.clients(api_connection.client_id).projects().create(id="my-project", name="Project")
    return (
      api_connection.clients(api_connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(
        name=random_string(),
      )
    )

  @pytest.fixture
  def training_run_guest_token(self, training_run, api_connection):
    return api_connection.training_runs(training_run.id).tokens().create().token

  @pytest.fixture
  def training_run_guest_url(self, training_run_guest_token):
    return "/guest?guest_token=" + training_run_guest_token


class TestGuestWebCreate(GuestWebTestBase):
  def test_guest_create(self, api_connection, web_connection, experiment, experiment_guest_url):
    response = web_connection.get(experiment_guest_url)
    assert experiment.name in response
    assert "End Session" not in response.body_html()
    for page in ("", "/analysis", "/history", "/suggestions", "/properties"):
      response = web_connection.get("/experiment/" + experiment.id + page)
      assert experiment.name in response
      assert "End Session" not in response.body_html()

  def test_training_run_guest_create(self, api_connection, web_connection, training_run, training_run_guest_url):
    response = web_connection.get(training_run_guest_url)
    assert training_run.name in response
    assert "End Session" not in response.body_html()

  @pytest.fixture
  def cookie_testing_enabled(self, app_url, config_broker):
    if not config_broker.get("web.enable_decrypt_cookie_endpoint", False):
      pytest.skip()
    resp = requests.get(f"{app_url}/cookie", verify=False, timeout=5)
    if resp.status_code == HTTPStatus.NOT_FOUND:
      raise Exception(
        "The cookie decryption endpoint is not enabled (you might need to add the environment variable"
        " ALLOW_DECRYPT_COOKIE_ENDPOINT=1 to the web server)"
      )
    resp.raise_for_status()

  @flaky(max_runs=2)
  def test_guest_state_nesting(
    self,
    api_connection,
    logged_in_web_connection,
    experiment,
    experiment_guest_url,
    app_url,
    experiment_guest_token,
    cookie_testing_enabled,
  ):
    # pylint: disable=too-many-locals
    del cookie_testing_enabled
    logged_in_web_connection.get("/experiment/" + experiment.id)
    with api_connection.create_any_experiment() as second_experiment:
      second_guest_token = api_connection.experiments(second_experiment.id).tokens().create().token
      second_guest_url = "/guest?guest_token=" + second_guest_token

      response1 = logged_in_web_connection.get(experiment_guest_url)
      cookie1 = response1.response.headers["Set-Cookie"]
      cookie1_contents = requests.get(f"{app_url}/cookie", headers={"Cookie": cookie1}, verify=False, timeout=5).json()
      assert cookie1_contents["loginState"]["clientId"] is None
      assert cookie1_contents["loginState"]["organizationId"] is None
      assert cookie1_contents["loginState"]["apiToken"] == experiment_guest_token

      response2 = logged_in_web_connection.get(second_guest_url)
      cookie2 = response2.response.headers["Set-Cookie"]
      cookie2_contents = requests.get(f"{app_url}/cookie", headers={"Cookie": cookie2}, verify=False, timeout=5).json()
      assert cookie2_contents["loginState"]["clientId"] is None
      assert cookie2_contents["loginState"]["organizationId"] is None
      assert cookie2_contents["loginState"]["apiToken"] == second_guest_token

      assert cookie1_contents["loginState"]["parentState"] == cookie2_contents["loginState"]["parentState"]

  def test_logged_in_guest_create(self, api_connection, logged_in_web_connection, experiment, experiment_guest_url):
    logged_in_web_connection.get("/experiment/" + experiment.id)

    response = logged_in_web_connection.get(experiment_guest_url)
    assert experiment.name in response
    assert "End Session" in response.body_html()
    response = logged_in_web_connection.get("/experiment/" + experiment.id)
    assert experiment.name in response
    assert "End Session" in response.body_html()


class TestGuestWebDelete(GuestWebTestBase):
  def test_guest_delete(self, api_connection, web_connection, experiment_guest_token, experiment_guest_url):
    api_connection.tokens(experiment_guest_token).delete()
    web_response = web_connection.get(experiment_guest_url, raise_for_status=False)
    assert web_response.response.status_code == HTTPStatus.NOT_FOUND
    assert "This link has expired" in web_response

  def test_logged_in_guest_delete(
    self, api_connection, logged_in_web_connection, experiment_guest_token, experiment_guest_url
  ):
    api_connection.tokens(experiment_guest_token).delete()
    web_response = logged_in_web_connection.get(experiment_guest_url, raise_for_status=False)
    assert web_response.response.status_code == HTTPStatus.NOT_FOUND
    assert "This link has expired" in web_response


class TestGuestWebInvalidate(GuestWebTestBase):
  def test_invalidate(self, api_connection, web_connection, experiment_guest_token, experiment_guest_url, experiment):
    web_connection.get(experiment_guest_url)
    web_connection.get("/experiment/" + experiment.id)
    api_connection.tokens(experiment_guest_token).delete()
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/experiment/" + experiment.id)
    assert "End Session" not in web_connection.get("/").body_html()

  def test_expire(self, db_connection, web_connection, experiment_guest_token, experiment_guest_url, experiment):
    web_connection.get(experiment_guest_url)
    web_connection.get("/experiment/" + experiment.id)
    token = db_connection.first(db_connection.query(Token).filter(Token.token == experiment_guest_token))
    meta = copy_protobuf(token.meta)
    meta.date_created = 1
    token.meta = meta
    db_connection.upsert(token)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get("/experiment/" + experiment.id)
    assert "End Session" not in web_connection.get("/").body_html()

  def test_logged_in_invalidate(
    self, api_connection, logged_in_web_connection, experiment_guest_token, experiment_guest_url, experiment
  ):
    logged_in_web_connection.get(experiment_guest_url)
    response = logged_in_web_connection.get("/experiment/" + experiment.id)
    assert response.get_csrf_token()
    assert "End Session" in response.body_html()
    api_connection.tokens(experiment_guest_token).delete()
    response = logged_in_web_connection.get("/experiment/" + experiment.id)
    assert response.get_csrf_token()
    assert "End Session" not in response.body_html()
