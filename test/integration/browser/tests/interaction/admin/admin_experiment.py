# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from integration.browser.tests.browser_test import BrowserTest


class TestExperimentAdmin(BrowserTest):
  def test_experiment(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    experiment = api_connection.create_any_experiment()
    driver.get_path(f"/experiment/{experiment.id}/admin")
    driver.wait_while_present(css_selector=".spinner")

  def test_param_importances_update_fail(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    experiment = api_connection.create_any_experiment()
    driver.get_path(f"/experiment/{experiment.id}/admin")
    driver.find_and_click(element_text="Update importances")
    driver.wait_for_element_by_css_selector(".alert-danger")

  def test_param_importances_update(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    parameters = [
      {"name": "a", "type": "double", "bounds": {"min": 1, "max": 10}},
      {"name": "b", "type": "double", "bounds": {"min": 1, "max": 10}},
    ]
    experiment = api_connection.create_any_experiment(parameters=parameters)
    for _ in range(10):
      s = api_connection.experiments(experiment.id).suggestions().create()
      api_connection.experiments(experiment.id).observations().create(
        suggestion=s.id,
        no_optimize=True,
        values=[{"value": 5}],
      )
    driver.get_path(f"/experiment/{experiment.id}/admin")
    driver.wait_while_present(css_selector=".spinner")
    driver.find_and_click(element_text="Update importances")
    driver.wait_for_element_by_css_selector(".alert-success")
