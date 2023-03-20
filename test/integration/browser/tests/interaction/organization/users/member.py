# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.invite.constant import ADMIN_ROLE

from integration.browser.tests.interaction.organization.users.test_base import UsersTestBase
from integration.utils.random_email import generate_random_email


class TestUsersAsMember(UsersTestBase):
  def run_permissions_test(self, driver):
    driver.wait_while_present(css_selector=".modal.fade.in .add-permission-row")

    self.select_role(driver, ADMIN_ROLE)
    self.expect_alert(driver)
    assert (
      driver.find_element_by_css_selector(".modal.fade.in .table-role-cell .dropdown .dropdown-btn-label").text
      == "Admin"
    )

    driver.find_and_click(css_selector=".modal.fade.in .edit-permission-row .delete-button")
    self.expect_alert(driver)
    driver.wait_while_present(css_selector=".modal.fade.in .edit-permission-row")

    driver.find_and_click(css_selector=".modal.fade.in .add-client-button")
    driver.wait_for_element_by_css_selector(".modal.fade.in .add-permission-row")
    driver.find_element_by_css_selector(
      ".modal.fade.in .add-permission-row .table-client-cell .dropdown-toggle[disabled]"
    )
    self.select_role(driver, ADMIN_ROLE, ".add-permission-row")
    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .cancel-button")

    driver.find_and_click(css_selector=".modal.fade.in .add-client-button")
    self.select_role(driver, ADMIN_ROLE, ".add-permission-row")
    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .accept-button")
    self.expect_alert(driver)

    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")
    assert len(driver.find_elements_by_css_selector(".modal.fade.in .edit-permission-row")) == 1

    driver.find_and_click(css_selector=".modal.fade.in .edit-permission-row .delete-button")
    self.expect_alert(driver)

    assert not driver.find_elements_by_css_selector(".modal.fade.in .edit-permission-row")
    driver.find_and_click(css_selector='.modal.fade.in [data-dismiss="modal"]')
    driver.wait_while_present(css_selector=".modal.fade.in")

  def test_client_filter_disabled(
    self,
    member_login_state,
    logged_in_member_driver,
    read_user,
    another_client,
  ):
    driver = logged_in_member_driver
    self.load_users_page(driver)

    driver.wait_for_element_by_css_selector(".memberships-section .table-search-holder .dropdown-toggle[disabled]")

  def test_no_editing_own_permissions(self, member_login_state, logged_in_member_driver):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    self.open_edit_modal(driver, member_login_state.email, "membership")

    driver.find_element_by_css_selector(".modal.fade.in .table-role-cell .dropdown .dropdown-toggle[disabled]")
    driver.find_element_by_css_selector(".modal.fade.in .delete-button[disabled]")

  def test_owner_edit(self, logged_in_member_driver, owner_user):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    driver.find_element_by_css_selector(
      f'.membership.table-row[data-id="{owner_user.email}"] .edit-button.btn-disabled'
    )
    driver.wait_while_present(css_selector=".membership.table-row .uninvite-button")

  def test_owner_invite_invisible(self, api_connection, logged_in_member_driver, owner_invite):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    driver.wait_while_present(css_selector=f'.invite.table-row[data-id="{owner_invite.email}"]')

  def test_edit_member_permissions(self, logged_in_member_driver, read_user):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    self.open_edit_modal(driver, read_user.email, "membership")

    self.run_permissions_test(driver)

  def test_no_uninvite_member(self, logged_in_member_driver, read_user):
    driver = logged_in_member_driver
    self.load_users_page(driver)

    driver.wait_while_present(css_selector=f'.membership.table-row[data-id="{read_user.email}"] .uninvite-button')

  def test_edit_member_invite_permissions(self, logged_in_member_driver, member_invite):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    self.open_edit_modal(driver, member_invite.email, "invite")

    self.run_permissions_test(driver)

  def test_no_remove_member_invite(self, logged_in_member_driver, member_invite):
    driver = logged_in_member_driver
    self.load_users_page(driver)

    driver.wait_while_present(css_selector=f'.invite.table-row[data-id="{member_invite.email}"] .uninvite-button')

  def test_create_invite(self, member_login_state, logged_in_member_driver, another_client):
    driver = logged_in_member_driver
    self.load_users_page(driver)
    self.open_create_invite_modal(driver)

    driver.find_element_by_css_selector('.modal.fade.in input[type="email"]').send_keys(
      member_login_state.email.upper()
    )
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')
    self.expect_alert(driver, alert_type="danger")

    driver.find_element_by_css_selector('.modal.fade.in input[type="email"]').clear()
    driver.find_element_by_css_selector('.modal.fade.in input[type="email"]').send_keys(generate_random_email())
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')

    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")
    driver.wait_for_element_by_css_selector(".modal.fade.in .add-permission-row")
    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .accept-button")
    self.expect_alert(driver)

    self.run_permissions_test(driver)

  def test_user_detail_with_team_admin(self, logged_in_member_driver, read_user):
    driver = logged_in_member_driver
    self.load_users_page(driver)

    driver.wait_for_element_by_css_selector("tr.table-row a.user-detail-link")
    num_of_users = len(driver.find_elements_by_css_selector("tr.table-row a.user-detail-link"))

    for i in range(min(num_of_users, 3)):
      driver.wait_for_element_by_css_selector("tr.table-row a.user-detail-link")
      element = driver.find_elements_by_css_selector("tr.table-row a.user-detail-link")[i]
      user = element.text
      element.click()

      element = driver.find_element_by_css_selector("dl.dl-horizontal dd:nth-child(4)")
      assert element.text == user

      driver.back()
