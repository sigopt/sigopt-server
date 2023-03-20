# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestAnalysis(ExperimentBrowserTest):
  def test_analysis_page_no_data(self, logged_in_driver, experiment):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment, "Analysis", "/analysis")

    driver.wait_for_element_by_xpath('//*[@class="history-chart"]/*[contains(text(), "no data")]')
    driver.wait_for_element_by_xpath('//*[@class="history-chart-4d"]/*[contains(text(), "no data")]')
    driver.wait_for_element_by_xpath('//*[@class="experiment-improvement"]/*[contains(text(), "no data")]')
    driver.wait_for_element_by_xpath('//*[@class="importance-table"]/*[contains(text(), "insufficient data")]')
    driver.wait_while_present(css_selector=".plotly")

  def test_analysis_page_with_data(self, logged_in_driver, experiment_with_data):
    driver = logged_in_driver
    self.navigate_to_experiment_page(driver, experiment_with_data, "Analysis", "/analysis")

    driver.wait_for_element_by_css_selector(".history-chart .plotly")
    driver.wait_for_element_by_css_selector(".experiment-improvement .plotly")
    driver.wait_for_element_by_css_selector(".parcoords-chart .plotly")
    driver.wait_for_element_by_xpath('//*[@class="importance-table"]/*[contains(text(), "insufficient data")]')
