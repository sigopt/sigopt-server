# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.project.test_base import ProjectBrowserTest


class TestProjectDetailPage(ProjectBrowserTest):
  def test_logged_out_not_found(self, driver, project):
    driver.get_path(f"/projects/{project.id}", title_text="Content Not Found - SigOpt")

  def test_project_page(self, logged_in_driver, project):
    driver = logged_in_driver
    driver.get_path(f"/project/{project.id}/experiments")
    driver.wait_for_element_by_css_selector(".no-experiments")
    assert len(driver.find_elements_by_css_selector(".experiment-row")) == 0

  def test_project_page_code(self, logged_in_driver, project):
    driver = logged_in_driver
    self.navigate_to_project_page(driver, project)
    driver.find_and_click(css_selector=".btn-inverse")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    for language, lines in [
      ("Python", ["import sigopt", f'sigopt.set_project("{project.id}")']),
    ]:
      driver.find_and_click(css_selector=".modal.fade.in .language-selector .dropdown-toggle")
      driver.find_and_click(css_selector=f".modal.fade.in .language-selector .{language}")
      code_block_text = driver.find_element_by_css_selector(".modal-body .code-block").text
      for line in lines:
        assert line in code_block_text

  def test_project_page_with_experiments(self, logged_in_driver, project_with_experiments):
    driver = logged_in_driver
    driver.get_path(f"/project/{project_with_experiments.id}/experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    assert len(driver.find_elements_by_css_selector(".no-experiments")) == 0
