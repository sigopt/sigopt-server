# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.auth import AuthProvider
from integration.web.test_base import WebBase


class TestTokenWeb(WebBase):
  @pytest.fixture
  def experiment(self, api_connection):
    return api_connection.create_any_experiment()

  @pytest.fixture
  def guest_token(self, experiment, api_connection):
    return api_connection.experiments(experiment.id).tokens().create().token

  def test_token_rotate(self, api_connection, web_connection, experiment, guest_token):
    guest_url = "/guest?guest_token=" + guest_token
    valid_old_token_response = web_connection.get(guest_url)
    assert experiment.name in valid_old_token_response
    new_token = api_connection.tokens(guest_token).update(token="rotate").token
    experiment_response = web_connection.get("/experiment/" + experiment.id, raise_for_status=False)
    assert experiment_response.response.status_code == HTTPStatus.NOT_FOUND
    assert experiment.name not in experiment_response
    invalid_old_token_response = web_connection.get(guest_url, raise_for_status=False)
    assert invalid_old_token_response.response.status_code == HTTPStatus.NOT_FOUND
    assert "This link has expired" in invalid_old_token_response
    new_token_response = web_connection.get("/guest?guest_token=" + new_token)
    assert experiment.name in new_token_response

  def test_token_revoke(self, api_connection, logged_in_web_connection, login_state, experiment):
    logged_in_web_connection.get("/experiment/" + experiment.id)
    api_connection.sessions().update(
      **{
        "email": login_state.email,
        "old_password": login_state.password,
        "new_password": AuthProvider.randomly_generated_password(),
      }
    )
    response = logged_in_web_connection.get("/experiment/" + experiment.id, raise_for_status=False)
    assert response.response.status_code == HTTPStatus.NOT_FOUND
