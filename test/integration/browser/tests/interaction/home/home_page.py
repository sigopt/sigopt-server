# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.interaction.experiment.list import ExperimentBrowserTest


class TestPage(ExperimentBrowserTest):
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

  def create_project(self, api_connection):
    return (
      api_connection.clients(api_connection.client_id)
      .projects()
      .create(
        name="Test Project",
        id="test-project",
      )
    )

  def get_header_names(self, driver, selector):
    header_elements = driver.find_elements_by_css_selector(selector)
    return [element.text for element in header_elements]

  def test_no_new_user_wizard(self, logged_in_driver):
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_while_present(css_selector=".spinner")
    driver.wait_while_present(css_selector=".wizard-carousel")

  def test_home_page(self, logged_in_driver):
    driver = logged_in_driver
    driver.get_path("/login")
    driver.wait_while_present(css_selector=".spinner")
    driver.wait_for_element_by_css_selector(css_selector=".experiment-list")
    assert self.get_header_names(driver, "div.title")[0] == "Home"

    # Check for null state of home page
    subheaders = self.get_header_names(driver, "h2")
    assert ["Recent Activity", "Learn More"] == subheaders

  def test_home_page_has_my_run(self, api_connection, logged_in_driver, other_connection):
    driver = logged_in_driver
    project = self.create_project(api_connection)
    # Create a run
    run = (
      api_connection.clients(api_connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(
        name="Test run",
      )
    )
    driver.get_path("/home")
    driver.wait_while_present(css_selector=".spinner")
    subheaders = self.get_header_names(driver, "h2")
    assert ["Recent Activity", "Learn More"] == subheaders
    assert run.name == driver.find_elements_by_css_selector(".recent-activity .title")[0].text

  def test_home_page_has_my_exp(self, api_connection, logged_in_driver):
    driver = logged_in_driver
    # Create "my" experiment
    exp = api_connection.create_experiment(
      dict(
        name="test experiment",
        parameters=[
          dict(name="a", type="int", bounds=dict(min=1, max=50)),
          dict(name="b", type="double", bounds=dict(min=-50, max=0)),
        ],
      )
    )
    driver.get_path("/home")
    driver.wait_while_present(css_selector=".spinner")
    subheaders = self.get_header_names(driver, "h2")
    expected = ["Recent Activity", "Learn More"]
    assert expected == subheaders
    assert exp.name == driver.find_elements_by_css_selector(".recent-activity .title")[0].text
