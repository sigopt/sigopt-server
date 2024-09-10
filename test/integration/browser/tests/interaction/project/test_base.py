# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import pytest

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META


class ProjectBrowserTest(ExperimentBrowserTest):
  @pytest.fixture
  def project(self, api_connection):
    return api_connection.clients(api_connection.client_id).projects().create(name="Test Project", id="test-project")

  @pytest.fixture
  def project_with_experiments(self, api_connection, unicode_experiment_meta):
    project = (
      api_connection.clients(api_connection.client_id)
      .projects()
      .create(
        name="Test Project with experiments",
        id="test-project-w-exps",
      )
    )
    for _ in range(5):
      meta = deepcopy(DEFAULT_AI_EXPERIMENT_META)
      meta["name"] = f'{meta["name"]} for testing projects'
      api_connection.clients(project.client).projects(project.id).aiexperiments().create(**meta)
    return project

  @pytest.fixture
  def project_with_experiments_and_run(self, api_connection, unicode_experiment_meta):
    project = (
      api_connection.clients(api_connection.client_id)
      .projects()
      .create(
        name="Test Project with experiments and runs",
        id="test-project-w-exps-w-runs",
      )
    )
    api_connection.clients(api_connection.client_id).projects(project.id).training_runs().create(
      name="Test run",
    )
    for _ in range(5):
      meta = deepcopy(DEFAULT_AI_EXPERIMENT_META)
      meta["name"] = f'{meta["name"]} for testing projects'
      api_connection.clients(project.client).projects(project.id).aiexperiments().create(**meta)
    return project

  # @classmethod
  # def check_project_detail_page(cls, driver, project_name, project_id):
  #   assert driver.find_element_by_css_selector('[data-field-name="project-name"] > div > span').text == project_name
  #   assert driver.find_element_by_css_selector('dd[data-field-name="project-id"]').text == project_id

  # @classmethod
  # def check_project_detail_page_pw(cls, page, project_name, project_id):
  #   assert page.locator('[data-field-name="project-name"] > div > span').inner_text() == project_name
  #   assert page.locator('dd[data-field-name="project-id"]').inner_text() == project_id

  # @classmethod
  # def navigate_to_project_page(cls, driver, project, **kwargs):
  #   real_path = f"/project/{project.id}"
  #   driver.get_path(real_path, title_text=f"{project.name} - Overview - SigOpt", **kwargs)
  #   cls.check_project_detail_page(driver, project_name=project.name, project_id=project.id)

  # @classmethod
  # def create_project_test(cls, page, start_selector, routes, client_id):
  #   page.click(start_selector)
  #   page.wait_for_selector(".modal.fade.in")
  #   page.click(".modal-footer .btn-primary")
  #   page.click(".alert-danger .close")
  #   page.locator("#project-name-input").fill("Test Project Create")
  #   assert page.eval_on_selector("#project-id-input", "e => e.value") == "test-project-create"
  #   page.locator("#project-id-input").fill("TEST()+=PROJECT;123")
  #   assert page.eval_on_selector("#project-id-input", "e => e.value") == "testproject123"
  #   page.locator("#project-name-input").fill("Test Project")
  #   assert page.eval_on_selector("#project-id-input", "e => e.value") == "testproject123"
  #   with page.expect_navigation(url=routes.get_full_url(f"/client/{client_id}/project/testproject123/overview")):
  #     page.click(".modal-footer .btn-primary")
  #   assert page.title() == "Test Project - Overview - SigOpt"
  #   cls.check_project_detail_page_pw(page, project_name="Test Project", project_id="testproject123")
  #   page.is_hidden(".experiment-row")
