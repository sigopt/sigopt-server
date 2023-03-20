# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestList(ExperimentBrowserTest):
  PAGE_SIZE = 10
  SEARCH_TOOLS_PREFIX = "div.search-tools-wrapper"

  @pytest.fixture
  def other_connection(self, api_connection, config_broker, api, auth_provider):
    login_state = self.make_login_state(auth_provider, has_verified_email=True)
    api_connection.clients(api_connection.client_id).invites().create(
      email=login_state.email,
      role="admin",
      old_role="uninvited",
    )
    login_state.client_id = api_connection.client_id
    login_state.client_token = None
    return self.make_api_connection(config_broker, api, login_state)

  def setup_experiments(self, api_connection, other_connection):
    e1_name, e2_name, e3_name, e4_name = (f"Experiment {name}" for name in ("ABC", "DEF", "GHI", "JKL"))
    api_connection.create_any_experiment(name=e1_name)
    e2 = api_connection.create_any_experiment(name=e2_name)
    api_connection.experiments(e2.id).delete()
    other_connection.create_any_experiment(name=e3_name, client_id=api_connection.client_id)
    e4 = other_connection.create_any_experiment(name=e4_name, client_id=api_connection.client_id)
    other_connection.experiments(e4.id).delete()
    return {
      "my-active": [e1_name],
      "my-all": [e1_name, e2_name],
      "team-active": [e1_name, e3_name],
      "team-all": [e1_name, e2_name, e3_name, e4_name],
    }
