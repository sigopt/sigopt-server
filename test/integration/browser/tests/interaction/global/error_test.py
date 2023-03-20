# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from integration.browser.tests.browser_test import BrowserTest


class TestAlertBrokerErrors(BrowserTest):
  def test_unexpected_error(self, driver):
    driver.get_path("/nsickness")
    driver.wait_while_present(css_selector=".alert-danger")
    driver.find_and_click(element_text="Trigger test error")
    driver.wait_for_element_by_css_selector(css_selector=".alert-danger")

  def test_token_expires(self, logged_in_driver, api_connection, login_state):
    with api_connection.create_any_experiment() as e:
      logged_in_driver.get_path(f"/experiment/{e.id}/suggestions")
      logged_in_driver.wait_while_present(css_selector=".history-table-row")
      logged_in_driver.find_and_click(element_text="Generate Suggestion")
      logged_in_driver.wait_for_element_by_css_selector(css_selector=".history-table-row")
      logged_in_driver.wait_while_present(css_selector=".alert-danger")
      logged_in_driver.wait_while_present(css_selector=".alert-warning")

      api_connection.sessions().update(
        old_password=login_state.password,
        new_password=login_state.password + "1",
      )

      logged_in_driver.find_and_click(element_text="Generate Suggestion")
      logged_in_driver.wait_for_element_by_css_selector(css_selector=".alert-danger")
      logged_in_driver.wait_while_present(css_selector=".alert-warning")

  def test_lose_write_permissions(
    self,
    api_connection,
    driver,
    login_state,
    web_connection,
    auth_provider,
  ):
    email = auth_provider.randomly_generated_email()
    password = auth_provider.randomly_generated_password()
    client_id = login_state.client_id
    organization_id = login_state.organization_id
    user_id, _ = auth_provider.create_user_tokens(email=email, password=password, has_verified_email=True)
    auth_provider.create_membership(user_id, organization_id)
    auth_provider.create_permission(user_id, client_id, WRITE)
    web_connection.login_as(email=email, password=password)
    driver.web_connection = web_connection
    driver.login()

    with api_connection.create_any_experiment(client_id=client_id) as e:
      driver.get_path(f"/experiment/{e.id}/suggestions")
      driver.wait_while_present(css_selector=".history-table-row")
      driver.find_and_click(element_text="Generate Suggestion")
      driver.wait_for_element_by_css_selector(css_selector=".history-table-row")
      driver.wait_while_present(css_selector=".alert-danger")
      driver.wait_while_present(css_selector=".alert-warning")

      # Reset the user to be read-only
      api_connection.clients(client_id).invites().create(
        email=email,
        old_role="user",
        role="read-only",
      )

      driver.find_and_click(element_text="Generate Suggestion")
      driver.wait_for_element_by_css_selector(css_selector=".alert-danger")
      driver.wait_while_present(css_selector=".alert-warning")
