# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.utils.random_assignment import rand_param


class TestSuggestions(ExperimentBrowserTest):
  def floats_approx_equal(self, a, b):
    return abs(a - b) < 1e-6

  def test_suggestions_load(self, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(
      driver,
      e,
      "Suggestions",
      "/suggestions",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_element_by_css_selector(f".modal.fade.in table .table-row:nth-child({len(e.parameters)})")
    driver.find_element_by_text("Created")

  def test_delete_suggestion(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(
      driver,
      e,
      "Suggestions",
      "/suggestions",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .delete-btn")
    driver.wait_for_element_by_css_selector(css_selector=".alert-info")

    suggestions = api_connection.experiments(e.id).suggestions().fetch()
    assert suggestions.count == 0

    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.wait_while_present(css_selector=".history-table-row")

  def test_create_suggestion(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(driver, e, "Suggestions", "/suggestions")
    time.sleep(1)
    driver.find_and_click(element_text="Generate Suggestion")
    driver.wait_for_element_by_css_selector(css_selector=".alert-success", wait_time=20)

    suggestions = api_connection.experiments(e.id).suggestions().fetch()
    assert suggestions.count == 2

    driver.wait_for_element_by_css_selector(".history-table-row:nth-child(2)")

  def test_generate_and_delete_queued_suggestion(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(driver, e, "Suggestions", "/suggestions")
    time.sleep(1)
    driver.find_and_click(css_selector="button.queued-suggestion-button")

    driver.wait_for_element_by_css_selector(".modal.fade.in", wait_time=20)

    assignments = dict()
    for param in e.parameters:
      param_value = rand_param(param)
      if param.type == "categorical":
        categorical_param_select = driver.find_element_by_css_selector(f".modal.fade.in select[name='{param.name}']")
        driver.set_select_option(categorical_param_select, param_value)
      else:
        driver.find_and_send_keys(css_selector=f".modal.fade.in input[name='{param.name}']", keys=str(param_value))
      assignments[param.name] = param_value

    queued_suggestions = api_connection.experiments(e.id).queued_suggestions().fetch()
    assert queued_suggestions.count == 0

    driver.find_and_click(css_selector=".modal.fade.in .submit-btn")
    driver.wait_for_element_by_css_selector(".alert-success")
    driver.find_and_click(css_selector=".modal.fade.in .close")
    driver.wait_while_present(css_selector=".modal-backdrop.fade.in")
    driver.wait_for_element_by_css_selector(".queued-suggestion-section .history-table-row")

    queued_suggestions = api_connection.experiments(e.id).queued_suggestions().fetch()
    assert queued_suggestions.count == 1

    queued_suggestion = queued_suggestions.data[0]

    for param in e.parameters:
      if param.type == "categorical":
        assert queued_suggestion.assignments[param.name] == assignments[param.name]
      else:
        assert self.floats_approx_equal(queued_suggestion.assignments[param.name], assignments[param.name])

    driver.find_and_click(css_selector=".queued-suggestion-section .history-table-row")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .delete-btn")
    driver.wait_for_element_by_css_selector(".alert-info")

    queued_suggestions = api_connection.experiments(e.id).queued_suggestions().fetch()
    assert queued_suggestions.count == 0

    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.wait_while_present(css_selector=".queued-suggestion-section .history-table-row")

  def test_submit_observation(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(
      driver,
      e,
      "Suggestions",
      "/suggestions",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")
    driver.find_and_send_keys(css_selector=".modal.fade.in .metric-section input.value", keys="100")
    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")

    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-success")
    driver.find_and_click(css_selector=".modal.fade.in .close")
    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.wait_while_present(css_selector=".history-table-row")

    observations = api_connection.experiments(e.id).observations().fetch()
    assert observations.count == 1
    observation = observations.data[0]
    assert observation.values[0].value == 100

  def test_submit_failed_observation(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    e = experiment_with_suggestions
    self.navigate_to_experiment_page(
      driver,
      e,
      "Suggestions",
      "/suggestions",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")
    driver.find_and_click(css_selector=".modal.fade.in .metric-failure input.failure-input")
    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")

    driver.wait_for_element_by_css_selector(".alert-success")
    driver.find_and_click(css_selector=".modal.fade.in .close")

    observations = api_connection.experiments(e.id).observations().fetch()
    assert observations.count == 1

    observation = observations.data[0]
    assert observation.value is None
    assert observation.failed

    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.wait_while_present(css_selector=".history-table-row")

  def test_parallel_bandwidth_banner(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    api_connection.experiments(experiment_with_suggestions.id).suggestions().create()

    driver.get_path(f"/experiment/{experiment_with_suggestions.id}/suggestions")
    driver.wait_for_element_by_css_selector(".parallel-bandwidth-warning")

  def test_no_banner_no_suggestions(self, api_connection, logged_in_driver, experiment):
    driver = logged_in_driver

    e = api_connection.experiments(experiment.id).fetch()
    assert e.parallel_bandwidth is None

    driver.get_path(f"/experiment/{experiment.id}/suggestions")
    driver.wait_while_present(".parallel-bandwidth-warning")

  def test_no_parallel_bandwidth_banner(self, api_connection, logged_in_driver, experiment_with_suggestions):
    driver = logged_in_driver
    api_connection.experiments(experiment_with_suggestions.id).update(parallel_bandwidth=3)

    driver.get_path(f"/experiment/{experiment_with_suggestions.id}/suggestions")
    driver.wait_while_present(".parallel-bandwidth-warning")
