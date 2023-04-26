# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest


class TestList(ExperimentBrowserTest):
  # pylint: disable=too-many-public-methods
  PAGE_SIZE = 10
  SEARCH_TOOLS_PREFIX = "div.search-tools-wrapper"

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

  def setup_experiments(self, api_connection, other_connection):
    e1_name, e2_name, e3_name, e4_name = (f"Experiment {name}" for name in ("ABC", "DEF", "GHI", "JKL"))
    api_connection.create_any_experiment(name=e1_name)
    e2 = api_connection.create_any_experiment(name=e2_name)
    api_connection.experiments(e2.id).delete()
    other_connection.create_any_experiment(name=e3_name, client_id=api_connection.client_id)
    e4 = other_connection.create_any_experiment(name=e4_name, client_id=api_connection.client_id)
    other_connection.experiments(e4.id).delete()
    return {
      "my-active": [e1_name],
      "my-all": [e1_name, e2_name],
      "team-active": [e1_name, e3_name],
      "team-all": [e1_name, e2_name, e3_name, e4_name],
    }

  def check_mine_and_team(self, driver, labels, experiment_groups):
    buttons = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} button")
    assert len(buttons) == 2
    for (key, label), button in zip(labels, buttons):
      button.click()
      driver.wait_for_element_by_xpath(f"//*[@data-experiment-view='{label}']")
      driver.wait_for_element_by_css_selector(".experiment-row")
      assert len(driver.find_elements_by_css_selector(".experiment-row")) == len(experiment_groups[key])
      for experiment_name in experiment_groups[key]:
        assert driver.find_element_by_text(experiment_name)

  def test_list_mine_team_buttons(self, api_connection, logged_in_driver, other_connection):
    experiment_groups = self.setup_experiments(api_connection, other_connection)
    driver = logged_in_driver
    driver.get_path("/experiments")
    labels = [("my-active", "mine"), ("team-active", "team")]
    self.check_mine_and_team(driver, labels, experiment_groups)

  def test_mine_team_logic_no_experiments(self, logged_in_driver):
    # There are no experiments in the team
    driver = logged_in_driver
    driver.get_path("/experiments")
    driver.wait_while_present(css_selector=".spinner")
    active_button = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} * .active-button")
    assert active_button.text == "Mine"

  def test_mine_team_logic_only_team_experiments(self, api_connection, logged_in_driver, other_connection):
    # A team member creates an experiment
    driver = logged_in_driver
    other_connection.create_any_experiment(name="ABC", client_id=api_connection.client_id)
    driver.get_path("/experiments")
    driver.wait_while_present(css_selector=".spinner")
    active_button = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} * .active-button")
    assert active_button.text == "Team"

  def test_mine_team_logic_mine_team_experiments(self, api_connection, logged_in_driver, other_connection):
    # Both the user and a team member create experiments
    other_connection.create_any_experiment(name="ABC", client_id=api_connection.client_id)
    api_connection.create_any_experiment(name="DEF")
    driver = logged_in_driver
    driver.get_path("/experiments")
    driver.wait_while_present(css_selector=".spinner")
    active_button = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} * .active-button")
    assert active_button.text == "Mine"

  def test_mine_team_logic_respect_filters(self, api_connection, logged_in_driver):
    # If a filter is turned on, refreshing the page the mine/team logic shouldn't switch mine/team
    api_connection.create_any_experiment(name="GHI")
    driver = logged_in_driver
    driver.get_path("/experiments?page=0&includeClient=true&archived=true")
    driver.wait_while_present(css_selector=".spinner")
    active_button = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} * .active-button")
    assert active_button.text == "Team"

  def test_list_archived_filter(self, api_connection, logged_in_driver, other_connection):
    experiment_groups = self.setup_experiments(api_connection, other_connection)
    driver = logged_in_driver
    driver.get_path("/experiments")
    labels = [("my-all", "mine"), ("team-all", "team")]
    driver.wait_for_element_by_css_selector(".experiment-row")
    filter_toggles = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle")
    archive_toggle = filter_toggles[0]
    archive_toggle.click()

    driver.wait_for_element_by_css_selector(".experiment-row")
    filters = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle-wrapper")
    archived_filter = filters[0]
    assert archived_filter.text == "Show Archived"
    archive_input = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} #archive-toggle")
    assert archive_input.is_selected()
    self.check_mine_and_team(driver, labels, experiment_groups)

  def test_list_development_filter(self, api_connection, development_api_connection, logged_in_driver):
    prod_name, dev_name = "some prod exp", "some dev exp"
    development_api_connection.create_any_experiment(name=dev_name)
    api_connection.create_any_experiment(name=prod_name)
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")

    driver.wait_for_element_by_css_selector(".experiment-row")
    assert len(driver.find_elements_by_css_selector(".experiment-row")) == 1
    assert driver.find_element_by_text(prod_name)

    filter_toggles = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle")
    dev_toggle = filter_toggles[1]
    dev_toggle.click()
    driver.wait_for_element_by_css_selector(".experiment-row")

    filters = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle-wrapper")
    dev_filter = filters[1]
    assert dev_filter.text == "Show Development"
    dev_input = driver.find_element_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} #dev-toggle")
    assert dev_input.is_selected()
    assert len(driver.find_elements_by_css_selector(".experiment-row")) == 2
    for experiment_name in [prod_name, dev_name]:
      assert driver.find_element_by_text(experiment_name)

  def test_select_one(self, api_connection, logged_in_driver):
    api_connection.create_any_experiment()
    api_connection.create_any_experiment()
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    select_boxes = driver.find_elements_by_css_selector(".experiment-row .checkbox label")
    assert len(select_boxes) == 2

    select_boxes[0].click()
    bulk_action_label = driver.find_element_by_css_selector(".bulk-action-label")
    assert bulk_action_label.text == "1 experiment selected"

    select_boxes[1].click()
    bulk_action_label = driver.find_element_by_css_selector(".bulk-action-label")
    assert bulk_action_label.text == "2 experiments selected"

    # clicking again needs to de-select
    select_boxes[0].click()
    bulk_action_label = driver.find_element_by_css_selector(".bulk-action-label")
    assert bulk_action_label.text == "1 experiment selected"

  def test_select_all(self, api_connection, logged_in_driver):
    api_connection.create_any_experiment()
    api_connection.create_any_experiment()
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    select_all_box = driver.find_element_by_css_selector("th .checkbox label")

    select_all_box.click()
    bulk_action_label = driver.find_element_by_css_selector(".bulk-action-label")
    assert bulk_action_label.text == "2 experiments selected"

    select_all_box.click()
    assert len(driver.find_elements_by_css_selector(".bulk-action-label")) == 0

  def test_act_on_selected(self, api_connection, logged_in_driver):
    api_connection.create_any_experiment()
    api_connection.create_any_experiment()
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    select_all_box = driver.find_element_by_css_selector("th .checkbox label")
    select_all_box.click()
    bulk_action_buttons = driver.find_elements_by_css_selector(".bulk-button-holder button")
    archive_button = bulk_action_buttons[0]

    archive_button.click()
    driver.wait_while_present(".bulk-button-holder")
    driver.wait_while_present(".spinner")
    driver.wait_while_present(css_selector=".experiment-row")

    filter_toggles = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle")
    archive_toggle = filter_toggles[0]
    archive_toggle.click()
    driver.wait_while_present(css_selector=".spinner")
    driver.wait_for(lambda d: len(d.find_elements_by_css_selector(".experiment-row")) == 2)

    select_all_box = driver.find_element_by_css_selector("th .checkbox label")
    select_all_box.click()
    bulk_action_buttons = driver.find_elements_by_css_selector(".bulk-button-holder button")
    unarchive_button = bulk_action_buttons[1]
    unarchive_button.click()
    driver.wait_while_present(".bulk-button-holder")
    driver.wait_while_present(".spinner")

    # turn archive filter off - show they appear on active page again
    filter_toggles = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} .filter-toggle")
    archive_toggle = filter_toggles[0]
    archive_toggle.click()
    driver.wait_while_present(".spinner")
    driver.wait_for_element_by_css_selector(".experiment-row")
    driver.wait_for(lambda d: len(d.find_elements_by_css_selector(".experiment-row")) == 2)

  def test_created_by_column(self, api_connection, logged_in_driver):
    api_connection.create_any_experiment()
    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    assert len(driver.find_elements_by_css_selector(".user-name-span")) == 0

    buttons = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} button")
    team_button = buttons[1]
    team_button.click()
    driver.wait_while_present(".spinner")
    driver.wait_for_element_by_css_selector(".experiment-row")
    assert len(driver.find_elements_by_css_selector(".user-name-span")) == 1

  def test_experiment_list_with_only_failed_obseravtions(self, api_connection, logged_in_driver):
    e = api_connection.create_any_experiment()
    s = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(suggestion=s.id, failed=True)

    driver = logged_in_driver
    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_for_element_by_css_selector(".experiment-row")
    best_values = driver.find_elements_by_css_selector(".metric-value")
    assert len(best_values) == 1
    assert best_values[0].text == "N/A"

  def test_experiment_list_history_remembers_page_on_browser_back(self, api_connection, logged_in_driver):
    driver = logged_in_driver
    for i in range(0, TestList.PAGE_SIZE + 2):
      api_connection.create_any_experiment(name=f"Experiment {i}")

    driver.get_path("/experiments?page=0", css_selector=".experiment-row")
    driver.wait_while_present(css_selector=".spinner")
    first_page = [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]

    driver.get_path("/experiments?page=1", css_selector=".experiment-row")
    driver.wait_while_present(css_selector=".spinner")
    second_page = [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]

    assert set(first_page) != set(second_page)

    buttons = driver.find_elements_by_css_selector(f"{self.SEARCH_TOOLS_PREFIX} button")
    team_button = buttons[1]
    team_button.click()
    driver.wait_while_present(css_selector=".spinner")
    driver.back()
    driver.wait_while_present(css_selector=".spinner")
    results = [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]
    assert results == second_page

  def test_experiment_search_searches_all_experiments(self, api_connection, logged_in_driver, other_connection):
    driver = logged_in_driver
    other_user = other_connection.users(other_connection.user_id).fetch()

    match_title = "flurble"
    api_connection.create_any_experiment(name=f"Match mine {match_title}")
    api_connection.create_any_experiment(name=f"No match on mine but has your name{other_user.name}")
    my_archived_experiment = api_connection.create_any_experiment(name=f"Match mine archived {match_title}")
    api_connection.experiments(my_archived_experiment.id).delete()
    other_connection.create_any_experiment(name=f"Match yours {match_title}", client_id=api_connection.client_id)
    other_connection.create_any_experiment(name="No match on yours", client_id=api_connection.client_id)
    your_archived_experiment = other_connection.create_any_experiment(
      name=f"Your archived {match_title}",
      client_id=api_connection.client_id,
    )
    other_connection.experiments(your_archived_experiment.id).delete()

    driver.get_path(f"/experiments?query={match_title}", css_selector=".experiment-row")
    driver.wait_while_present(css_selector=".spinner")
    assert "4 results found out of 6" in driver.find_element_by_css_selector(".search-metadata-holder").text
    search_results = driver.find_elements_by_css_selector(".experiment-name")
    for result in search_results:
      assert match_title in result.text

    driver.get_path(f"/experiments?query={other_user.name}", css_selector=".experiment-row")
    driver.wait_while_present(css_selector=".spinner")
    assert "4 results found out of 6" in driver.find_element_by_css_selector(".search-tools-wrapper").text
    search_titles = [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]
    search_authors = [result.text for result in driver.find_elements_by_css_selector(".experiment-row .user-name-span")]
    for title, author in zip(search_titles, search_authors):
      assert other_user.name in title or other_user.name in author

  def test_experiment_search_pagination_history(self, api_connection, logged_in_driver):
    # pylint: disable=too-many-locals
    driver = logged_in_driver

    def find_all_by_pagination(target):
      back_stack = []
      found: list[str] = []

      while True:
        driver.wait_while_present(css_selector=".spinner")
        found.extend(result.text for result in driver.find_elements_by_css_selector(".experiment-name"))
        cur_page_indicators = driver.find_elements_by_css_selector(".pagination .active a")
        back_stack.append(
          {
            "page": cur_page_indicators[0].text if cur_page_indicators else None,
            "state": [result.text for result in driver.find_elements_by_css_selector(".experiment-name")],
          }
        )
        disabled_nexts = driver.find_elements_by_css_selector("li.disabled a.next")
        nexts = driver.find_elements_by_css_selector("a.next")
        if disabled_nexts or not nexts:
          break
        nexts[0].click()

      assert set(found) == set(target)
      return back_stack

    search_1_match = "flurple"
    search_2_match = "dooby"
    search_1_results = [f"{name} {i}" for i, name in enumerate([search_1_match] * 4)]
    search_2_results = [f"{name} {i}" for i, name in enumerate([search_2_match] * 11)]

    for experiment_name in search_1_results + search_2_results:
      api_connection.create_any_experiment(name=experiment_name)

    back_stack = []

    driver.get_path("/experiments")
    back_stack.extend(find_all_by_pagination(search_1_results + search_2_results))

    for match, targets in zip([search_1_match, search_2_match], [search_1_results, search_2_results]):
      # Click twice in order to highlight all text in search box, workaround for clear=True in driver
      driver.find_and_click(css_selector=".search-wrapper .search-input")
      driver.find_and_click(css_selector=".search-wrapper .search-input")
      driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys="", clear=True)
      driver.wait_while_present(css_selector=".search-all-item")
      driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys=match)
      driver.wait_while_present(css_selector=".spinner")
      search_all = driver.find_element_by_css_selector(".search-all-item")
      search_all.click()
      driver.wait_while_present(css_selector=".spinner")
      back_stack.extend(find_all_by_pagination(targets))

    while back_stack:
      cur_page_indicators = driver.find_elements_by_css_selector(".pagination .active a")
      cur_page = cur_page_indicators[0].text if cur_page_indicators else None
      results = [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]
      memory = back_stack.pop()
      assert memory["page"] == cur_page
      assert memory["state"] == results
      driver.back()
      driver.wait_while_present(css_selector=".spinner")

  def test_experiment_search_unmatched_parameters(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    def get_results_for_url(url):
      driver.get_path(url, css_selector=".experiment-row")
      driver.wait_while_present(css_selector=".spinner")
      return [result.text for result in driver.find_elements_by_css_selector(".experiment-name")]

    match = "urple"
    for i in range(TestList.PAGE_SIZE + 1):
      api_connection.create_any_experiment(name=f"{match} {i}")

    dashboard = get_results_for_url("/experiments")
    results = get_results_for_url("/experiments?query=&page=garbage")
    assert results == dashboard
    search_first_page = get_results_for_url(f"/experiments?query={match}&page=0")
    results = get_results_for_url(f"/experiments?query={match}&page=garbage")
    assert results == search_first_page
    results = get_results_for_url(f"/experiments?includeClient=true&query={match}")
    assert results == search_first_page

    results = get_results_for_url("/experiments?fakeField=garbage&page=10")
    assert results == dashboard
    results = get_results_for_url("/experiments?page=10000")
    assert results == dashboard

  def test_search_box(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    current_user = api_connection.users(api_connection.user_id).fetch()
    dummy_experiment = "Dummy Experiment #1"
    search_term = dummy_experiment[:5].lower()
    api_connection.create_any_experiment(name=dummy_experiment)

    driver.get_path("/experiments", title_text="Experiments", css_selector=".search-wrapper")

    driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys=search_term, clear=True)
    driver.wait_for_element_by_css_selector(css_selector=".search-box-menu-item")

    dropdown_options = driver.find_elements_by_css_selector(".search-box-menu-item .experiment-name")
    assert len(dropdown_options) == 2
    search_all_option = dropdown_options[0]
    assert search_all_option.text == f"Search all results for {search_term}"
    assert dropdown_options[1].text == dummy_experiment

    search_all_option.click()
    driver.wait_while_present(css_selector=".spinner")
    search_results = driver.find_elements_by_css_selector(".experiment-name")
    assert len(search_results) == 1
    assert search_results[0].text == dummy_experiment

    driver.get_path("/experiments", title_text="Experiments")

    driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys=current_user.name, clear=True)
    driver.wait_for_element_by_css_selector(css_selector=".search-box-menu-item")

    assert len(driver.find_elements_by_css_selector(".search-box-menu-item")) == 2
    experiment_result_option = driver.find_elements_by_css_selector(".search-box-menu-item .experiment-name")[1]
    experiment_result_option.click()
    driver.wait_while_present(css_selector=".spinner")
    assert driver.find_element_by_css_selector(".title").text == dummy_experiment

    api_connection.create_any_experiment(name="Search Integration Test Experiment")

    driver.get_path("/experiments", title_text="Experiments")

    driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys="integration", clear=True)
    driver.wait_for_element_by_css_selector(css_selector=".search-box-menu-item")

    # Dummy Experiment #1 and Search Integration Test Experiment show up because the username contains "integration"
    assert len(driver.find_elements_by_css_selector(".search-box-menu-item")) == 3

    driver.get_path("/experiments", title_text="Experiments")

    driver.find_and_send_keys(css_selector=".search-wrapper .search-input", keys="abcdefg", clear=True)
    driver.wait_for_element_by_css_selector(css_selector=".search-box-menu .no-results")
    assert len(driver.find_elements_by_css_selector(".search-box-menu-item")) == 0

  def test_force_identical_query_reload(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    match = "load_twice"
    num_matches = 5
    assert num_matches < TestList.PAGE_SIZE - 1
    for i in range(num_matches):
      api_connection.create_any_experiment(name=f"{match} {i}")

    driver.get_path(f"/experiments?query={match}", title_text="Experiments")
    driver.wait_while_present(css_selector=".spinner")
    search_results = driver.find_elements_by_css_selector(".experiment-name")
    assert len(search_results) == num_matches

    api_connection.create_any_experiment(name=f"{match} {num_matches + 1}")

    driver.find_and_click(css_selector=".search-wrapper .search-input")
    driver.wait_for_element_by_css_selector(css_selector=".search-all-item")
    driver.find_and_click(css_selector=".search-all-item")
    driver.wait_while_present(css_selector=".spinner")
    search_results = driver.find_elements_by_css_selector(".experiment-name")
    assert len(search_results) == num_matches + 1

  def test_archive_experiment(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    experiment = api_connection.create_any_experiment(name="Dummy Experiment #1")

    driver.get_path("/experiments", title_text="Experiments", css_selector=".experiment-row")

    driver.find_and_click(css_selector=".experiment-row .dropup > .dropdown-toggle")
    driver.wait_for_element_by_css_selector(".experiment-row .dropup.open")
    driver.find_and_click(css_selector=".experiment-row .dropup .archive")

    driver.wait_for_element_by_css_selector(".no-experiments")

    e = api_connection.experiments(experiment.id).fetch()
    assert e.state == "deleted"

  def test_share_experiment(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    api_connection.create_any_experiment(name="Dummy Experiment #1")
    api_connection.create_any_experiment(name="Dummy Experiment #2")

    driver.get_path("/experiments", title_text="Experiments", css_selector=".experiment-row")

    driver.find_and_click(css_selector=".experiment-row .dropup > .dropdown-toggle")
    driver.wait_for_element_by_css_selector(".experiment-row .dropup.open")
    driver.find_and_click(css_selector=".experiment-row .dropup .share")

    driver.wait_for_element_by_css_selector(css_selector=".modal .share-experiment-row")

  def test_url_params(self, api_connection, logged_in_driver):
    driver = logged_in_driver

    for i in range(TestList.PAGE_SIZE + 1):
      api_connection.create_any_experiment(name=f"Dummy Experiment {i}")

    driver.get_path("/experiments?page=1", css_selector=".experiment-row")

    assert len(driver.find_elements_by_css_selector(".experiment-row")) == 1
    assert driver.find_element_by_css_selector(".experiment-name").text == "Dummy Experiment 0"

  def test_quick_start_guide(self, logged_in_driver):
    driver = logged_in_driver

    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_while_present(css_selector=".spinner")
    driver.find_element_by_css_selector(".quick-start-guide")

  def test_no_quick_start_guide(self, api_connection, logged_in_driver):
    driver = logged_in_driver
    api_connection.create_any_experiment(name="Experiment #1")

    driver.get_path("/experiments", title_text="Experiments")
    driver.wait_while_present(css_selector=".spinner")
    driver.wait_while_present(css_selector=".quick-start-guide")
