# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.utils.random_assignment import rand_param


class TestAddData(ExperimentBrowserTest):
  def set_report_table_assignments(self, page, e):
    for param in e.parameters:
      param_value = rand_param(param)
      if param.type == "categorical":
        page.select_option(f"select[name='{param.name}']", param_value)
      else:
        page.type(f"input[name='{param.name}']", str(param_value))

  def get_report_table_assignments(self, page, e):
    assignments = dict()
    for param in e.parameters:
      if param.type == "categorical":
        value = page.eval_on_selector(f"select[name='{param.name}']", "el => el.value")
      else:
        value = page.input_value(f"input[name='{param.name}']")
      assignments[param.name] = value
    return assignments

  def test_create_observation(self, api_connection, logged_in_page, experiment, routes):
    page = logged_in_page
    e = experiment
    page.goto(routes.get_full_url(f"/experiment/{e.id}/report"))
    self.set_report_table_assignments(page, e)
    assignments = self.get_report_table_assignments(page, e)
    page.type("input.value", "10.2")
    page.click(".submit-button")
    page.wait_for_selector(".alert-success")

    observation = api_connection.experiments(e.id).observations().fetch(limit=1).data[0]
    assert observation.values[0].value == 10.2

    for param in e.parameters:
      if param.type == "categorical":
        assert observation.assignments[param.name] == assignments[param.name]
      else:
        assert observation.assignments[param.name] == float(assignments[param.name])

  def test_create_failed_observation(self, api_connection, logged_in_page, experiment, routes):
    page = logged_in_page
    e = experiment
    page.goto(routes.get_full_url(f"/experiment/{e.id}/report"))
    self.set_report_table_assignments(page, e)
    assignments = self.get_report_table_assignments(page, e)
    page.type("input.value", "10.2")
    page.click("input.failure-input")
    page.click(".submit-button")
    page.wait_for_selector(".alert-success")

    observation = api_connection.experiments(e.id).observations().fetch(limit=1).data[0]
    assert observation.value is None
    assert observation.failed

    for param in e.parameters:
      if param.type == "categorical":
        assert observation.assignments[param.name] == assignments[param.name]
      else:
        assert observation.assignments[param.name] == float(assignments[param.name])
