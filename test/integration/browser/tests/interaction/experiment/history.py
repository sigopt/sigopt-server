# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestHistory(ExperimentBrowserTest):
  def test_history_page_no_data(self, logged_in_driver, experiment):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment, "History", "/history")
    assert len(driver.find_elements_by_css_selector(".history-table-row")) == 0

  def test_history_page_with_data(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    assert len(driver.find_elements_by_css_selector(".history-table-row")) == 3

  def test_update_metric(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_element_by_css_selector(".modal.fade.in .metric-failure")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")

    driver.find_and_click(css_selector=".modal.fade.in .failure-input")

    value_input = driver.find_element_by_css_selector(".modal.fade.in .metric-view .td-value input.value")
    value_input.clear()
    value_input.send_keys("1e")
    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-danger")
    driver.find_and_click(css_selector=".modal.fade.in .alert-danger .close")
    value_input.clear()
    value_input.send_keys("1e3")

    stddev_input = driver.find_element_by_css_selector(
      ".modal.fade.in .metric-view .td-value_stddev input.value_stddev"
    )
    stddev_input.clear()
    stddev_input.send_keys("1e")
    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-danger")
    driver.find_and_click(css_selector=".modal.fade.in .alert-danger .close")
    stddev_input.clear()
    stddev_input.send_keys("1e-1")

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    assert driver.find_element_by_css_selector(".modal.fade.in .metric-view .td-value").text == "1000"
    assert driver.find_element_by_css_selector(".modal.fade.in .metric-view .td-value_stddev").text == "±0.1"

    driver.find_and_click(css_selector=".modal.fade.in .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in")

    assert (
      driver.find_element_by_css_selector(".history-table-row:nth-child(1) td:nth-child(2) .number-value").text
      == "1000"
    )
    assert (
      driver.find_element_by_css_selector(".history-table-row:nth-child(1) td:nth-child(3) .number-value").text == "0.1"
    )

  def test_update_metric_pw(self, logged_in_page, experiment_with_data, routes):
    page = logged_in_page
    page.goto(routes.get_full_url(f"/experiment/{experiment_with_data.id}/history"))
    page.click(".history-table-row:nth-child(1) td:nth-child(1)")
    page.wait_for_selector(".modal.fade.in .metric-failure")
    page.click(".modal.fade.in .edit-btn")

    page.click(".modal.fade.in .failure-input")

    value_input = page.locator(".modal.fade.in .metric-view .td-value input.value")
    value_input.fill("1e")
    page.click(".modal.fade.in .finish-btn")
    page.click(".modal.fade.in .alert-danger .close")
    value_input.fill("1e3")

    stddev_input = page.locator(".modal.fade.in .metric-view .td-value_stddev input.value_stddev")
    stddev_input.fill("1e")
    page.click(".modal.fade.in .finish-btn")
    page.click(".modal.fade.in .alert-danger .close")
    stddev_input.fill("1e-1")

    page.click(".modal.fade.in .finish-btn")
    page.wait_for_selector(".modal.fade.in .alert-info")

    page.wait_for_selector(".modal.fade.in .metric-view .td-value >> text='1000'")
    page.wait_for_selector(".modal.fade.in .metric-view .td-value_stddev >> text='±0.1'")

    page.click(".modal.fade.in .modal-header .close")

    page.wait_for_selector(".history-table-row:nth-child(1) td:nth-child(2) .number-value >> text='1000'")
    page.wait_for_selector(".history-table-row:nth-child(1) td:nth-child(3) .number-value >> text='0.1'")

  def test_update_metric_failure(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(2) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.wait_while_present(css_selector=".modal.fade.in .metric-failure")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .delete-btn")

    driver.find_and_click(css_selector=".modal.fade.in .failure-label")
    driver.wait_for_element_by_css_selector(".modal.fade.in .failure-label.failed")
    driver.wait_for_element_by_css_selector(".modal.fade.in .metric-view .td-value .value[disabled]")
    driver.wait_for_element_by_css_selector(".modal.fade.in .metric-view .td-value_stddev .value_stddev[disabled]")

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    assert driver.find_element_by_css_selector(".modal.fade.in .metric-failure .field-value h2").text == "Failed"

    driver.find_and_click(css_selector=".modal.fade.in .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in")

    assert (
      driver.find_element_by_css_selector(".history-table-row:nth-child(2) td:nth-child(2) .failure-value").text
      == "Observation failed"
    )

  @pytest.mark.parametrize(
    "parameter_index,input_value,expected_value",
    [
      [1, "0.0", "0"],
      [2, "1", "1"],
    ],
  )
  def test_update_numerical_assignment(
    self,
    logged_in_driver,
    experiment_with_data,
    parameter_index,
    input_value,
    expected_value,
  ):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")

    assignment_input = driver.find_element_by_css_selector(
      f".modal.fade.in tbody .table-row:nth-child({parameter_index}) .value input"
    )
    assignment_input.clear()
    assignment_input.send_keys(input_value)

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    assert (
      driver.find_element_by_css_selector(f".modal.fade.in tbody .table-row:nth-child({parameter_index}) .value").text
      == expected_value
    )

    driver.find_and_click(css_selector=".modal.fade.in .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in")

    assert (
      driver.find_element_by_css_selector(
        f".history-table-row:nth-child(1) td:nth-child({2 + parameter_index}) .number-value"
      ).text
      == expected_value
    )

  def test_update_categorical_assignment(
    self,
    logged_in_driver,
    experiment_with_data,
  ):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")

    driver.find_and_click(css_selector=".modal.fade.in tbody .table-row:nth-child(3) .value select")
    driver.find_and_click(css_selector=".modal.fade.in tbody .table-row:nth-child(3) .value select option:nth-child(2)")

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    assert driver.find_element_by_css_selector(".modal.fade.in tbody .table-row:nth-child(3) .value").text == "e🐧"

    driver.find_and_click(css_selector=".modal.fade.in .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in")

    assert (
      driver.find_element_by_css_selector(".history-table-row:nth-child(1) td:nth-child(5) .string-value").text == "e🐧"
    )

  def test_same_assignments_keeps_suggestion(
    self,
    logged_in_driver,
    experiment_with_data,
  ):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")

    driver.find_element_by_css_selector(".modal.fade.in .multi-report .suggestion-report")

    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")

    assignment_input = driver.find_element_by_css_selector(".modal.fade.in tbody .table-row:nth-child(1) .value input")
    value = assignment_input.get_attribute("value")
    assignment_input.clear()
    assignment_input.send_keys(value)

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    driver.find_element_by_css_selector(".modal.fade.in .multi-report .suggestion-report")

  def test_update_assignments_detaches_suggestion(
    self,
    logged_in_driver,
    experiment_with_data,
  ):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")

    driver.find_element_by_css_selector(".modal.fade.in .multi-report .suggestion-report")

    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")

    assignment_input = driver.find_element_by_css_selector(".modal.fade.in tbody .table-row:nth-child(2) .value input")
    assignment_input.clear()
    assignment_input.send_keys("3.14159")

    driver.find_and_click(css_selector=".modal.fade.in .finish-btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info")

    driver.wait_while_present(css_selector=".modal.fade.in .multi-report .suggestion-report")

  def test_history_page_delete(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(
      driver,
      experiment_with_data,
      "History",
      "/history",
      css_selector=".history-table-row",
    )
    driver.find_element_by_css_selector(".history-table-row:nth-child(3)")
    driver.find_and_click(css_selector=".history-table-row:nth-child(1) td:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal.fade.in .edit-btn")
    driver.find_and_click(css_selector=".modal.fade.in .delete-btn")
    driver.wait_while_present(".modal.fade.in")
    driver.wait_while_present(css_selector=".history-table-row:nth-child(3)")
