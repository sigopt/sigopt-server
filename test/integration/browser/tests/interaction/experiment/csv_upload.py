# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import tempfile

import pytest

from zigopt.handlers.experiments.observations.create import DEFAULT_MAX_OBSERVATIONS_CREATE_COUNT

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestUploadCSV(ExperimentBrowserTest):
  def get_csv_file(self, logged_in_web_connection, e):
    return logged_in_web_connection.get(f"/experiment/{e.id}/historydownload").response_text()

  @pytest.mark.slow
  def test_upload_csv(self, config_broker, logged_in_driver, logged_in_web_connection, api_connection, experiment):
    observation_count = config_broker.get(
      "features.maxObservationsCreateCount",
      DEFAULT_MAX_OBSERVATIONS_CREATE_COUNT,
    )
    driver = logged_in_driver
    s = api_connection.experiments(experiment.id).suggestions().create()
    for _ in range(observation_count):
      api_connection.experiments(experiment.id).observations().create(
        suggestion=s.id,
        no_optimize=True,
        values=[{"value": 1}],
      )
    assert api_connection.experiments(experiment.id).observations().fetch().count == observation_count
    csv_file = self.get_csv_file(logged_in_web_connection, experiment)
    with tempfile.NamedTemporaryFile("wb") as f:
      f.write(csv_file.encode("utf-8"))
      f.flush()
      path = f.name
      self.navigate_to_experiment_page(driver, experiment, "Bulk Data Entry", "/report/file")
      file_input = driver.find_element_by_xpath("//input[@class='file-input']")
      file_input.send_keys(path)
      submit = driver.find_element_by_css_selector("input[value='Import']")
      submit.click()
      driver.wait_while_present(".spinner", wait_time=35)
      driver.wait_for_element_by_css_selector(".alert-success", wait_time=30)
      assert api_connection.experiments(experiment.id).observations().fetch().count == 2 * observation_count
