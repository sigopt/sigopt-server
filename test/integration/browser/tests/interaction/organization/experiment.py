# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.models.test_error import FindElementErrorInTest
from integration.browser.tests.interaction.organization.test_base import OrganizationTestBase


class TestExperiments(OrganizationTestBase):
  def count_clients_in_dropdown(self, driver):
    driver.find_and_click(css_selector=".client-filter .dropdown")
    driver.wait_for_element_by_css_selector(".dropdown.open li")
    count = len(driver.find_elements_by_css_selector('.dropdown.open li[role="presentation"]'))
    driver.find_and_click(css_selector=".client-filter .dropdown")
    return count

  def test_multiple_client_organization(self, logged_in_driver, another_client, write_user, api_connection, services):
    del write_user
    driver = logged_in_driver

    api_connection.create_any_experiment()
    api_connection.create_any_experiment()

    driver.get_path(
      "/organization/experiments", title_text="Organization Experiments", css_selector=".experiments-info"
    )
    driver.wait_while_present(css_selector=".spinner")

    num_user_rows = len(driver.find_elements_by_xpath('.//div[@id="users-table"]/table/tbody/tr'))
    assert num_user_rows == 2
    num_team_rows = len(driver.find_elements_by_xpath('.//div[@id="teams-table"]/table/tbody/tr'))
    assert num_team_rows == 2
    num_experiment_rows = len(driver.find_elements_by_css_selector(".recent-experiments-table tbody tr"))
    assert num_experiment_rows == 2

    num_clients_in_organization = services.client_service.count_by_organization_id(api_connection.organization_id)
    assert self.count_clients_in_dropdown(driver) == num_clients_in_organization + 1
    driver.find_and_click(css_selector=".client-filter .dropdown")
    driver.find_and_click(css_selector=f'.client-filter .dropdown.open [data-id="{another_client.id}"]')
    driver.wait_while_present(css_selector=".spinner")

    num_user_rows = len(driver.find_elements_by_xpath('.//div[@id="users-table"]/table/tbody/tr'))
    assert num_user_rows == 1
    empty_cell = driver.find_element_by_css_selector(".recent-experiments-table tbody tr p")
    assert empty_cell

  def test_single_client_organization(self, logged_in_driver, api_connection):
    driver = logged_in_driver

    api_connection.create_any_experiment()
    api_connection.create_any_experiment()

    driver.get_path(
      "/organization/experiments", title_text="Organization Experiments", css_selector=".experiments-info"
    )
    driver.wait_while_present(css_selector=".spinner")

    with pytest.raises(FindElementErrorInTest):
      driver.find_element_by_css_selector(".client-filter .dropdown")

    num_team_rows = len(driver.find_elements_by_xpath('.//div[@id="teams-table"]/table/tbody/tr'))
    assert num_team_rows == 1
    num_user_rows = len(driver.find_elements_by_xpath('.//div[@id="users-table"]/table/tbody/tr'))
    assert num_user_rows == 1
    num_experiment_rows = len(driver.find_elements_by_css_selector(".recent-experiments-table tbody tr"))
    assert num_experiment_rows
