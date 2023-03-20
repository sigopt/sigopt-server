# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.organization.test_base import OrganizationTestBase


class UsersTestBase(OrganizationTestBase):
  def load_users_page(self, driver):
    driver.get_path("/organization/users", title_text="Organization Users")
    driver.wait_for_element_by_css_selector(".membership.table-row")

  def open_create_invite_modal(self, driver):
    driver.find_and_click(css_selector=".invite-user button")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    return driver.find_element_by_css_selector(".modal.fade.in .modal-content")

  def open_edit_modal(self, driver, email, class_name="membership"):
    driver.find_and_click(css_selector=f'.{class_name}.table-row[data-id="{email}"] .edit-button')
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    return driver.find_element_by_css_selector(".modal.fade.in .modal-content")

  def open_uninvite_modal(self, driver, email, class_name="membership"):
    driver.find_and_click(css_selector=f'.{class_name}.table-row[data-id="{email}"] .uninvite-button')
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    return driver.find_element_by_css_selector(".modal.fade.in .modal-content")

  def count_membership_table_rows(self, driver, class_name="membership"):
    return len(driver.find_elements_by_css_selector(f".{class_name}.table-row"))

  def filter_invites(self, driver, filter_text):
    driver.find_element_by_css_selector(".invites-section .name-filter").send_keys(filter_text)

  def filter_memberships(self, driver, filter_text):
    driver.find_element_by_css_selector(".memberships-section .name-filter").send_keys(filter_text)

  def count_clients_in_dropdown(self, driver):
    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .table-client-cell .dropdown button")
    driver.wait_for_element_by_css_selector(".modal.fade.in .add-permission-row .table-client-cell .dropdown.open li")
    return len(
      driver.find_elements_by_css_selector(
        '.modal.fade.in .add-permission-row .table-client-cell .dropdown.open li[role="presentation"]'
      )
    )

  def select_role(self, driver, role, row=""):
    driver.find_and_click(css_selector=f".modal.fade.in {row} .table-role-cell .dropdown button")
    driver.find_and_click(
      css_selector=f'.modal.fade.in {row} .table-role-cell .dropdown.open [data-id="{role}"]',
    )

  def expect_alert(self, driver, alert_type="info"):
    driver.wait_for_element_by_css_selector(f".modal.fade.in .alert-{alert_type}", wait_time=20)
    driver.find_and_click(css_selector=f".modal.fade.in .alert-{alert_type} .close")
