# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from selenium.webdriver.common.by import By

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestSummary(ExperimentBrowserTest):
  @pytest.fixture
  def experiment_with_observation_budget(self, api_connection, unicode_experiment_meta):
    meta = unicode_experiment_meta
    meta["observation_budget"] = 100
    e = api_connection.create_experiment(meta)
    s = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 5}],
    )
    s = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 7}],
    )
    return e

  @pytest.fixture
  def multimetric_experiment(self, api_connection, unicode_experiment_meta):
    meta = unicode_experiment_meta
    meta["observation_budget"] = 100
    meta["metrics"] = [{"name": "first metric"}, {"name": "second metric"}]
    e = api_connection.create_experiment(meta)
    for i in range(3):
      s = api_connection.experiments(e.id).suggestions().create()
      api_connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=[{"name": "first metric", "value": i + 1}, {"name": "second metric", "value": 10 - i}],
      )
    return e

  def test_page_loads_with_title(self, logged_in_driver, experiment):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment, "Summary")
    elem = driver.find_element_by_css_selector(".title")
    assert elem.text == experiment.name

  def test_experiment_page_nav(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment_with_data, "Summary")

    nav = driver.find_element_by_css_selector(".experiment-nav")
    link = nav.find_element(By.LINK_TEXT, "Summary")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}")
    link = nav.find_element(By.LINK_TEXT, "Analysis")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/analysis")
    link = nav.find_element(By.LINK_TEXT, "Suggestions")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/suggestions")
    link = nav.find_element(By.LINK_TEXT, "History")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/history")
    link = nav.find_element(By.LINK_TEXT, "Add Data")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/report")
    link = nav.find_element(By.LINK_TEXT, "Properties")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/properties")
    assert nav.find_element(By.CSS_SELECTOR, ".active").text == "Summary"

  def test_page_loads_with_data(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment_with_data, "Summary")

    driver.find_element_by_css_selector(".improvement")
    driver.wait_for_element_by_css_selector(".experiment-improvement .plotly")
    driver.wait_for_element_by_css_selector(".history-table-row")
    assert len(driver.find_elements_by_css_selector(".history-table-row")) == 3

    link = driver.find_element_by_link_text("See All")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/history")
    link = driver.find_element_by_partial_link_text("More Graphs")
    assert link.get_attribute("href").endswith(f"/experiment/{experiment_with_data.id}/analysis")

    driver.find_element_by_partial_link_text("Share").click()
    driver.wait_for_element_by_css_selector(".modal.fade.in.share-modal")

    guest_url = driver.find_element_by_id("share-experiment-url-input").get_attribute("value")
    driver.get(guest_url)

    driver.wait_for_element_by_css_selector(".chart-holder")

  def test_page_loads_with_no_data(self, logged_in_driver, experiment):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment, "Summary")

    driver.find_element_by_partial_link_text("Share").click()
    driver.wait_for_element_by_css_selector(".modal.fade.in.share-modal")
    driver.find_element_by_css_selector(".share-modal")

    guest_url = driver.find_element_by_id("share-experiment-url-input").get_attribute("value")
    driver.get(guest_url)
    driver.wait_for_element_by_css_selector(".add-data-prompt")

    driver.find_element_by_text("To get started, ask a user with write permissions to add some data.")

  def test_development_experiment(self, logged_in_driver, development_experiment):
    driver = logged_in_driver
    driver.get_path(f"/experiment/{development_experiment.id}")
    driver.find_element_by_css_selector(".development-alert")

  def test_best_assignment_modal(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    driver.get_path(f"/experiment/{experiment_with_data.id}")

    driver.wait_for_element_by_css_selector(".value-section")
    driver.find_and_click(css_selector=".summary-holder")
    driver.wait_for_element_by_css_selector(".modal.fade.in")

    driver.find_element_by_css_selector(".modal.fade.in .metric-view")
    assert driver.find_element_by_css_selector(".modal.fade.in .metric-view .name").text == "Metric"

    num_params = len(experiment_with_data.parameters)
    driver.find_element_by_css_selector(f".modal.fade.in table .table-row:nth-child({num_params})")

    assert (
      driver.find_element_by_css_selector(
        ".modal.fade.in .observation-report .display-row:nth-child(1) .field-name"
      ).text
      == "Observation ID"
    )

  def test_experiment_summary_multimetric(self, logged_in_driver, api_connection, multimetric_experiment):
    driver = logged_in_driver
    driver.get_path(f"/experiment/{multimetric_experiment.id}")

    best_count = api_connection.experiments(multimetric_experiment.id).best_assignments().fetch().count
    driver.wait_for_element_by_css_selector(f".experiment-summary .table-card:nth-child({best_count})")
    driver.wait_while_present(css_selector=".value-section")

    driver.find_and_click(css_selector=".experiment-summary .table-card:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in")

    assert driver.find_element_by_css_selector(".modal.fade.in .metric-view:nth-child(1) .name").text == "first metric"
    assert driver.find_element_by_css_selector(".modal.fade.in .metric-view:nth-child(2) .name").text == "second metric"

    num_params = len(multimetric_experiment.parameters)
    driver.find_element_by_css_selector(f".modal.fade.in table .table-row:nth-child({num_params})")

  def test_experiment_history(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    driver.get_path(f"/experiment/{experiment_with_data.id}", css_selector=".recent-data .history-table")

    driver.find_and_click(css_selector=".recent-data .history-table .history-table-row:nth-child(1)")
    driver.wait_for_element_by_css_selector(".modal.fade.in .metric-failure")
    num_params = len(experiment_with_data.parameters)
    driver.find_element_by_css_selector(f".modal.fade.in table .table-row:nth-child({num_params})")

  def test_experiment_without_observation_budget(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    s = api_connection.experiments(experiment.id).suggestions().create()
    api_connection.experiments(experiment.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 5}],
    )
    s = api_connection.experiments(experiment.id).suggestions().create()
    api_connection.experiments(experiment.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 15}],
    )
    driver.get_path(f"/experiment/{experiment.id}")
    driver.wait_for_element_by_css_selector(".observation-warning")

  def test_experiment_with_observation_budget(self, logged_in_driver, experiment_with_observation_budget):
    driver = logged_in_driver
    driver.get_path(f"/experiment/{experiment_with_observation_budget.id}")

    observation_budget_progress = driver.find_element_by_css_selector(".observation-budget-progress")
    label_text = observation_budget_progress.find_element(By.CSS_SELECTOR, ".title-label").text
    assert str(experiment_with_observation_budget.observation_budget) in label_text
