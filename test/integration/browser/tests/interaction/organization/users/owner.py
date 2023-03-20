# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.invite.constant import ADMIN_ROLE
from zigopt.membership.model import MembershipType

from integration.browser.tests.interaction.organization.users.test_base import UsersTestBase
from integration.utils.random_email import generate_random_email


class TestUsersAsOwner(UsersTestBase):
  def run_permissions_test(self, driver, with_alerts):
    self.select_role(driver, ADMIN_ROLE)
    if with_alerts:
      self.expect_alert(driver)

    driver.wait_for(
      lambda d: d.find_element_by_css_selector(".modal.fade.in .table-role-cell .dropdown .dropdown-btn-label").text
      == "Admin"
    )

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
    if with_alerts:
      self.expect_alert(driver)

    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")

    deletes = driver.find_elements_by_css_selector(".modal.fade.in .edit-permission-row .delete-button")
    assert len(deletes) == 2
    deletes[1].click()

    if with_alerts:
      self.expect_alert(driver)

    assert len(driver.find_elements_by_css_selector(".modal.fade.in .edit-permission-row")) == 1

  def test_filter_invites_client(
    self,
    logged_in_driver,
    owner_invite,
    member_invite,
    another_client,
  ):
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver, "invite") == 2
    driver.find_and_click(css_selector=".invites-section .table-search-holder .dropdown")
    driver.wait_for_element_by_css_selector(".invites-section .table-search-holder .dropdown.open")
    assert (
      len(
        driver.find_elements_by_css_selector(
          '.invites-section .table-search-holder .dropdown.open [role="presentation"]'
        )
      )
      == 3
    )
    driver.find_and_click(
      css_selector=f'.invites-section .table-search-holder .dropdown.open [data-id="{another_client.id}"]'
    )
    assert self.count_membership_table_rows(driver, "invite") == 1

  def test_filter_memberships_client(
    self,
    login_state,
    logged_in_driver,
    admin_user,
    read_user,
    another_client,
  ):
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver, "membership") == 3
    driver.find_and_click(css_selector=".memberships-section .table-search-holder .dropdown")
    driver.wait_for_element_by_css_selector(".memberships-section .table-search-holder .dropdown.open")
    assert (
      len(
        driver.find_elements_by_css_selector(
          '.memberships-section .table-search-holder .dropdown.open [role="presentation"]'
        )
      )
      == 3
    )
    driver.find_and_click(
      css_selector=f'.memberships-section .table-search-holder .dropdown.open [data-id="{another_client.id}"]'
    )
    assert self.count_membership_table_rows(driver, "membership") == 1

  def test_filter_memberships_by_name(self, services, api_connection, auth_provider, logged_in_driver, owner_invite):
    user_name = "Filtered Users Name"
    self._make_user(
      services,
      MembershipType.owner,
      client_invites=[],
      api_connection=api_connection,
      auth_provider=auth_provider,
      name=user_name,
    )
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver, "membership") == 2
    self.filter_memberships(driver, user_name.upper())
    assert self.count_membership_table_rows(driver, "membership") == 1

  def test_filter_memberships_by_email(self, logged_in_driver, owner_invite, owner_user):
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver, "membership") == 2
    self.filter_memberships(driver, owner_user.email.upper())
    assert self.count_membership_table_rows(driver, "membership") == 1

  def test_filter_invites_by_email(self, logged_in_driver, owner_invite, owner_user):
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver, "invite") == 1
    self.filter_invites(driver, owner_invite.email.upper())
    assert self.count_membership_table_rows(driver, "invite") == 1

  def test_filter_all(self, logged_in_driver, owner_user, read_user):
    driver = logged_in_driver
    self.load_users_page(driver)
    assert self.count_membership_table_rows(driver) == 3
    self.filter_memberships(driver, "no user should match this string")
    assert self.count_membership_table_rows(driver) == 0

  def test_owner_modal(self, logged_in_driver, owner_user):
    driver = logged_in_driver
    self.load_users_page(driver)
    driver.find_element_by_css_selector(
      f'.membership.table-row[data-id="{owner_user.email}"] .edit-button.btn-disabled'
    )
    driver.wait_while_present(css_selector=".membership.table-row .uninvite-button")

  def test_remove_owner_invite(self, api_connection, logged_in_driver, owner_invite, services):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_uninvite_modal(driver, owner_invite.email, "invite")

    driver.wait_while_present(css_selector=".modal.fade.in .edit-permission-row")
    driver.wait_while_present(css_selector=".modal.fade.in .add-permission-row")
    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")

    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]', wait_time=20)

    driver.wait_while_present(css_selector=".modal.fade.in")

    driver.wait_while_present(css_selector=f'.invite.table-row[data-id="{owner_invite.email}"]')

    assert (
      services.invite_service.find_by_email_and_organization(
        owner_invite.email,
        int(api_connection.organization_id),
      )
      is None
    )

  def test_edit_member_permissions(self, logged_in_driver, read_user, another_client):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_edit_modal(driver, read_user.email, "membership")

    self.run_permissions_test(driver, with_alerts=True)

  def test_edit_member_invite_permissions(self, logged_in_driver, member_invite, another_client):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_edit_modal(driver, member_invite.email, "invite")

    self.run_permissions_test(driver, with_alerts=True)

  def test_uninvite_member(self, api_connection, logged_in_driver, login_state, read_user, services):
    driver = logged_in_driver
    self.load_users_page(driver)

    self.open_uninvite_modal(driver, read_user.email, "membership")
    assert driver.find_element_by_css_selector(".modal.fade.in .modal-header h4").text == f"Remove {read_user.name}"
    assert read_user.name in driver.find_element_by_css_selector(".modal.fade.in .modal-content").text

    self.load_users_page(driver)
    self.open_uninvite_modal(driver, read_user.email, "membership")
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')
    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.wait_while_present(css_selector=f'.membership.table-row[data-id="{read_user.email}"]')

    assert (
      services.membership_service.find_by_user_and_organization(
        read_user.id,
        int(api_connection.organization_id),
      )
      is None
    )

  def test_remove_member_invite(self, api_connection, logged_in_driver, member_invite, services):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_uninvite_modal(driver, member_invite.email, "invite")

    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')

    driver.wait_while_present(css_selector=".modal.fade.in")

    driver.wait_while_present(css_selector=f'.invite.table-row[data-id="{member_invite.email}"]')

    assert (
      services.invite_service.find_by_email_and_organization(
        member_invite.email,
        int(api_connection.organization_id),
      )
      is None
    )

  def test_create_member_invite(self, logged_in_driver, read_user, another_client, config_broker):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_create_invite_modal(driver)

    invite_email = generate_random_email()
    driver.find_element_by_css_selector('.modal.fade.in input[type="email"]').send_keys(invite_email)
    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")
    driver.find_element_by_css_selector(".modal.fade.in .add-permission-row")

    assert self.count_clients_in_dropdown(driver) == 2

    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .accept-button")

    self.run_permissions_test(driver, with_alerts=False)
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info", wait_time=20)

    alert = driver.find_element_by_css_selector(".modal.fade.in .alert-info")
    if config_broker.get("email.enabled", True):
      assert "?code=" not in alert.text
    else:
      assert "?code=" in alert.text

    driver.find_and_click(css_selector=".modal .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in", wait_time=20)
    driver.find_element_by_css_selector(f'.invite.table-row[data-id="{invite_email.lower()}"]')

  def test_reset_invite_state(self, logged_in_driver, another_client):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_create_invite_modal(driver)

    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .accept-button")
    driver.find_and_click(css_selector='.modal.fade.in .owner-check input[type="checkbox"]')
    driver.find_and_click(css_selector=".modal.fade.in .modal-header .close")
    driver.wait_for_element_by_css_selector('.modal.fade[style="display: none;"]')

    self.open_create_invite_modal(driver)

    checkbox = driver.find_element_by_css_selector('.modal.fade.in .owner-check input[type="checkbox"]')
    assert checkbox.get_attribute("checked") is None

    assert len(driver.find_elements_by_css_selector(".modal.fade.in .edit-permission-row")) == 0
    assert len(driver.find_elements_by_css_selector(".modal.fade.in .add-permission-row")) == 1

  def test_create_owner_invite(self, logged_in_driver, another_client):
    driver = logged_in_driver
    self.load_users_page(driver)
    self.open_create_invite_modal(driver)

    invite_email = generate_random_email()
    driver.find_element_by_css_selector('.modal.fade.in input[type="email"]').send_keys(invite_email)

    driver.wait_while_present(css_selector=".modal.fade.in .add-client-button")
    driver.find_element_by_css_selector(".modal.fade.in .add-permission-row")
    driver.find_and_click(css_selector=".modal.fade.in .add-permission-row .accept-button")
    self.run_permissions_test(driver, with_alerts=False)

    driver.find_and_click(css_selector='.modal.fade.in .owner-check input[type="checkbox"]')
    driver.find_and_click(css_selector='.modal.fade.in input[type="submit"]')
    driver.wait_for_element_by_css_selector(".modal.fade.in .alert-info", wait_time=20)

    driver.find_and_click(css_selector=".modal .modal-header .close")
    driver.wait_while_present(css_selector=".modal.fade.in", wait_time=20)
    driver.find_element_by_css_selector(f'.invite.table-row[data-id="{invite_email.lower()}"]')
