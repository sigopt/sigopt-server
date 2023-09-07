# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import re

import pytest
from selenium.webdriver.common.by import By

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestCreate(ExperimentBrowserTest):
  def submit_experiment_create(self, driver):
    driver.find_and_click(css_selector=".create-button")
    driver.wait_for_title_text("Experiment ABC - Summary - SigOpt")
    elem = driver.find_element_by_css_selector(".title")
    assert elem.text == "Experiment ABC"
    assert re.search(r"/experiment/\d+", driver.current_url)

  def test_create_experiment(self, logged_in_driver, config_broker):
    # pylint: disable=too-many-locals
    driver = logged_in_driver
    driver.get_path("/experiments/create", title_text="Create Experiment", css_selector=".experiment-creator")

    driver.find_and_send_keys(css_selector="[placeholder='Experiment Name']", keys="Experiment ABC")

    objective_type_selects = driver.find_elements_by_css_selector(".metric-table select")
    assert len(objective_type_selects) == 1
    for select, objective_type in zip(objective_type_selects, ["minimize", "maximize"]):
      driver.set_select_option(select, objective_type)

    # TODO: Test with multiple metrics
    metric_name_inputs = driver.find_elements_by_css_selector("[placeholder='Metric Name']")
    for i, metric_input in enumerate(metric_name_inputs):
      metric_input.send_keys("Metric" + str(i))

    driver.find_and_click(element_text="Add Parameter", repeat=2)
    parameter_type_selects = driver.find_elements_by_css_selector(".experiment-parameter-info select")
    assert len(parameter_type_selects) == 3
    for select, parameter_type in zip(parameter_type_selects, ("Categorical", "Decimal", "Integer")):
      driver.set_select_option(select, parameter_type)

    parameter_name_inputs = driver.find_elements_by_css_selector("[placeholder='Parameter Name']")
    for i, name_input in enumerate(parameter_name_inputs):
      name_input.send_keys("Param " + str(i))

    parameter_min_inputs = driver.find_elements_by_css_selector("[placeholder='Min']")
    for i, min_input in enumerate(parameter_min_inputs):
      min_input.send_keys(str(i - 50))

    parameter_max_inputs = driver.find_elements_by_css_selector("[placeholder='Max (Inclusive)']")
    for i, max_input in enumerate(parameter_max_inputs):
      max_input.send_keys(str(i + 50))

    categorical_value_input_wrapper = driver.find_element_by_css_selector(".categorical-value-input")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, "input").send_keys("abc")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, ".dropdown-item").click()
    driver.wait_for_element_by_css_selector(".rbt-token-removeable")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, "input").send_keys("def")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, ".dropdown-item").click()

    self.submit_experiment_create(driver)

  def test_create_fail_and_retry(self, logged_in_driver, api_connection):
    driver = logged_in_driver
    driver.get_path("/experiments/create", title_text="Create Experiment", css_selector=".experiment-creator")

    driver.find_and_send_keys(css_selector="[placeholder='Experiment Name']", keys="Experiment ABC")
    driver.find_and_send_keys(css_selector="[placeholder='Parameter Name']", keys="p")

    metric_name_inputs = driver.find_elements_by_css_selector("[placeholder='Metric Name']")
    for i, metric_input in enumerate(metric_name_inputs):
      metric_input.send_keys("Metric" + str(i))

    driver.find_and_click(css_selector=".create-button")
    driver.wait_for_element_by_css_selector(".alert.alert-danger")
    driver.find_and_click(css_selector=".alert .close")

    parameter_type_select = driver.find_element_by_css_selector(".experiment-parameter-info select")
    driver.set_select_option(parameter_type_select, "Categorical")
    categorical_value_input_wrapper = driver.find_element_by_css_selector(".categorical-value-input")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, "input").send_keys("abc")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, ".dropdown-item").click()
    driver.wait_for_element_by_css_selector(".rbt-token-removeable")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, "input").send_keys("def")
    categorical_value_input_wrapper.find_element(By.CSS_SELECTOR, ".dropdown-item").click()

    self.submit_experiment_create(driver)

  @pytest.mark.skipif(True, reason="TODO: works in Firefox not Chrome")
  def test_create_with_conditionals(self, logged_in_driver, api_connection):
    # pylint: disable=too-many-locals
    driver = logged_in_driver

    driver.get_path("/experiments/create", title_text="Create Experiment", css_selector=".experiment-creator")

    driver.find_and_send_keys(css_selector="[placeholder='Experiment Name']", keys="Experiment ABC")
    driver.find_and_send_keys(css_selector="[placeholder='Parameter Name']", keys="p")
    driver.find_and_send_keys(css_selector="[placeholder='Min']", keys=0)
    driver.find_and_send_keys(css_selector="[placeholder='Max (Inclusive)']", keys=1)

    conditionals_input = driver.find_element_by_css_selector(".experiment-conditionals-input")
    driver.find_and_click(css_selector=".experiment-conditionals-input .add-button", repeat=2)
    conditionals_name_inputs = conditionals_input.find_elements_by_css_selector('input[name="name"]')
    for i, html_input in enumerate(conditionals_name_inputs):
      html_input.send_keys(f"c{i}")

    for holder in conditionals_input.find_elements_by_css_selector(".add-value-button-holder"):
      holder.find_element_by_css_selector(".btn-add").click()

    conditionals_value_inputs = conditionals_input.find_elements_by_css_selector('input[name="value"]')
    for value, html_input in zip(["1", "2", "a", "b"], conditionals_value_inputs):
      html_input.send_keys(value)

    parameter_condition_inputs = conditionals_input.find_elements_by_css_selector(".parameter-input-holder")
    for param, html_input in zip([None, "p", "p", "p"], parameter_condition_inputs):
      if param is not None:
        html_input.find_element_by_css_selector("input").send_keys(param)
        html_input.find_element_by_css_selector(".dropdown-item").click()

    driver.find_and_click(css_selector=".create-button")
    driver.wait_for_title_text("Experiment ABC - Summary - SigOpt")
    match = re.search(r"/experiment/(\d+)", driver.current_url)
    assert match
    experiment_id = match.group(1)

    # TODO: some of these conditions are empty, we will remove that feature
    experiment = api_connection.experiments(experiment_id).fetch()
    (c0, c1) = sorted(experiment.conditionals, key=lambda c: c.name)
    assert c0.name == "c0"
    assert sorted(c0.values) == sorted(["1", "2"])
    assert c1.name == "c1"
    assert sorted(c1.values) == sorted(["a", "b"])
    (p,) = experiment.parameters
    conditions = p.conditions
    assert len(conditions) == 2
    assert conditions.c0 == ["2"]
    assert sorted(conditions.c1) == sorted(["a", "b"])
