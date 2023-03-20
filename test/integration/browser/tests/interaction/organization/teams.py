# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.organization.test_base import OrganizationTestBase


class TestTeams(OrganizationTestBase):
  def load_teams_page(self, driver):
    driver.get_path("/organization/teams", title_text="Organization Teams")

  def count_team_rows(self, driver):
    return len(driver.find_elements_by_css_selector(".section-content tbody tr"))

  def check_team_row_count(self, driver, count):
    assert self.count_team_rows(driver) == count

  def change_team_name_test(self, driver, client_id):
    self.load_teams_page(driver)
    row_selector = f'tr[data-id="{client_id}"]'
    edit_button_selector = f"{row_selector} .edit-button"
    driver.find_and_click(css_selector=edit_button_selector)
    input_selector = f'{row_selector} input[type="text"]'
    driver.find_element_by_css_selector(input_selector).clear()
    updated_team_name = "Updated Team Name"
    driver.find_element_by_css_selector(input_selector).send_keys(updated_team_name)
    driver.find_and_click(css_selector=f'{row_selector} button[type="submit"]')
    driver.wait_for_element_by_css_selector(edit_button_selector)
    assert driver.find_element_by_css_selector(f"{row_selector} .field-static > span").text == updated_team_name
    self.load_teams_page(driver)
    assert driver.find_element_by_css_selector(f"{row_selector} .field-static > span").text == updated_team_name

  def test_row_count_as_owner(self, logged_in_driver, another_client):
    self.load_teams_page(logged_in_driver)
    self.check_team_row_count(logged_in_driver, 2)

  def test_row_count_as_member(self, logged_in_member_driver, another_client):
    self.load_teams_page(logged_in_member_driver)
    self.check_team_row_count(logged_in_member_driver, 1)

  def test_change_team_name_as_owner(self, logged_in_driver, login_state):
    self.change_team_name_test(logged_in_driver, login_state.client_id)

  def test_change_team_name_as_member(self, logged_in_member_driver, member_login_state):
    self.change_team_name_test(logged_in_member_driver, member_login_state.client_id)

  def test_create_team_as_owner(self, login_state, logged_in_driver):
    driver = logged_in_driver
    self.load_teams_page(driver)
    self.check_team_row_count(logged_in_driver, 1)
    driver.find_and_click(css_selector=".section-button .btn")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    new_team_name = "New Team Name"
    input_selector = '.modal.fade.in input[type="text"]'
    driver.find_element_by_css_selector(input_selector).clear()
    driver.find_element_by_css_selector(input_selector).send_keys(new_team_name)
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')
    driver.wait_while_present(".modal.fade.in")
    driver.wait_for(lambda d: self.count_team_rows(d) == 2)
    self.load_teams_page(driver)
    self.check_team_row_count(logged_in_driver, 2)

  def test_create_team_button_hidden_as_member(self, logged_in_member_driver):
    driver = logged_in_member_driver
    self.load_teams_page(driver)
    driver.wait_while_present(".section-button .btn")
