# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesApiException
from integration.browser.tests.browser_test import BrowserTest


class TestGuestAccess(BrowserTest):
  @pytest.fixture(autouse=True)
  def cleanup_tokens(self, api_connection):
    for token in api_connection.clients(api_connection.client_id).tokens().fetch().iterate_pages():
      if not token.all_experiments:
        api_connection.tokens(token.token).delete()

  def check_guest_url(self, e, logged_in_driver, guest_url):
    # Ensure that the guest can see the experiment, but cannot change the experiment in any way
    logged_in_driver.get(guest_url)
    logged_in_driver.find_element_by_css_selector(".title")
    share_button = logged_in_driver.find_elements_by_css_selector(".share-experiment-btn")
    assert len(share_button) == 0
    logged_in_driver.find_and_click(element_text="End Session")
    logged_in_driver.get_path("/experiment/" + e.id)
    logged_in_driver.find_element_by_css_selector(".share-experiment-btn")

  def test_guest(self, api_connection, logged_in_driver):
    e = api_connection.create_any_experiment()
    # Report an observation
    suggestion = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(
      values=[{"value": 5.1}], suggestion=suggestion.id, no_optimize=True
    )

    # Create the guest token
    logged_in_driver.get_path(f"/experiment/{e.id}")

    # As items above the fold animate in, they appear to move the button around. So wait for them
    # to appear on the page before attempting to click
    logged_in_driver.wait_while_present(css_selector=".spinner")
    logged_in_driver.find_and_click(css_selector=".share-experiment-btn")

    logged_in_driver.wait_for_element_by_css_selector(css_selector="#share-experiment-url-input")
    url_input = logged_in_driver.find_element_by_id("share-experiment-url-input")
    guest_url = url_input.get_attribute("value")
    self.check_guest_url(e, logged_in_driver, guest_url)

  def test_guest_dashboard(self, logged_in_driver, api_connection):
    e = api_connection.create_any_experiment()
    # Report an observation
    suggestion = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(
      values=[{"value": 5.1}], suggestion=suggestion.id, no_optimize=True
    )

    logged_in_driver.get_path("/tokens/manage", css_selector=".generate-share-btn")
    logged_in_driver.find_and_click(css_selector=".generate-share-btn")
    logged_in_driver.wait_for_element_by_css_selector(".experiment-select")
    logged_in_driver.set_select_option(logged_in_driver.find_element_by_css_selector(".experiment-select"), e.id)
    logged_in_driver.find_and_click(css_selector=".generate-link-btn")
    logged_in_driver.wait_for_element_by_css_selector(".alert-success")
    logged_in_driver.wait_while_present(css_selector=".modal-backdrop.fade")
    logged_in_driver.find_and_click(css_selector=".alert-success .close")
    logged_in_driver.wait_while_present(css_selector=".alert-success")

    logged_in_driver.find_and_click(css_selector=".share-btn")
    logged_in_driver.wait_for_element_by_css_selector("#share-experiment-url-input")
    url_input = logged_in_driver.find_element_by_id("share-experiment-url-input")
    guest_url = url_input.get_attribute("value")
    self.check_guest_url(e, logged_in_driver, guest_url)

  def test_guest_dashboard_delete_token(self, logged_in_driver, api_connection):
    e = api_connection.create_any_experiment()
    token = api_connection.experiments(e.id).tokens().create().token
    api_connection.tokens(token).fetch()

    # Delete the token
    logged_in_driver.get_path("/tokens/manage", css_selector=".delete-btn")
    logged_in_driver.find_and_click(css_selector=".delete-btn")
    logged_in_driver.find_and_click(css_selector=".confirm-delete-btn")
    logged_in_driver.wait_while_present(css_selector=".modal-backdrop")

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      api_connection.tokens(token).fetch()
