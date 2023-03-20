# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.interaction.project.test_base import ProjectBrowserTest


class TestProjectList(ProjectBrowserTest):
  PAGE_SIZE = 12

  @pytest.fixture
  def other_connection(self, api_connection, config_broker, api, auth_provider):
    login_state = self.make_login_state(auth_provider, has_verified_email=True)
    api_connection.clients(api_connection.client_id).invites().create(
      email=login_state.email,
      role="admin",
      old_role="uninvited",
    )
    login_state.client_id = api_connection.client_id
    login_state.client_token = None
    return self.make_api_connection(config_broker, api, login_state)

  @pytest.fixture
  def project_groups(self, api_connection, other_connection):
    my_p = (
      api_connection.clients(api_connection.client_id)
      .projects()
      .create(
        name="My Test Project",
        id="my-test-project",
      )
    )
    archived_p = (
      api_connection.clients(api_connection.client_id)
      .projects()
      .create(
        name="My Archived Project",
        id="my-archived-project",
      )
    )
    api_connection.clients(archived_p.client).projects(archived_p.id).update(deleted=True)
    team_p = (
      other_connection.clients(other_connection.client_id)
      .projects()
      .create(
        name="Team Test Project",
        id="team-test-project",
      )
    )
    examples_p = api_connection.clients(api_connection.client_id).projects("sigopt-examples").fetch()
    return {
      "mine": [my_p],
      "mine_archived": [my_p, archived_p],
      "team": [my_p, team_p, examples_p],
      "team_archived": [my_p, archived_p, team_p, examples_p],
    }

  def check_mine_and_team(self, page, project_groups):
    for key, text in zip(["mine", "team"], ["Mine", "Team"]):
      page.click(f".view-button-wrapper >> text={text}")
      page.wait_for_selector(f"//*[@data-project-view='{key}']")
      for project in project_groups[key]:
        assert page.wait_for_selector(f'text="{project.name}"')

  def test_list_mine_team_buttons(self, logged_in_page, project_groups, routes):
    page = logged_in_page
    page.goto(routes.get_full_url("/projects"))
    self.check_mine_and_team(page, project_groups)

  def test_archived_button(self, logged_in_page, project_groups, routes):
    page = logged_in_page
    page.goto(routes.get_full_url("/projects"))
    page.wait_for_selector("//*[@data-project-view='mine']")
    for project in project_groups["mine"]:
      page.wait_for_selector(f'text="{project.name}"')
    page.click(".projects-show-archived-holder .filter-toggle")
    page.wait_for_selector("//*[@data-project-view='mine']")
    for project in project_groups["mine_archived"]:
      page.wait_for_selector(f'text="{project.name}"')

  def test_create_project(self, api_connection, logged_in_page, routes):
    page = logged_in_page
    page.goto(routes.get_full_url("/projects"))
    self.create_project_test(
      page,
      ".page-title-pre .btn-inverse",
      routes,
      api_connection.client_id,
    )
