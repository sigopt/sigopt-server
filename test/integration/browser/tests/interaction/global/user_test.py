# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from time import sleep

import pytest

from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE
from zigopt.membership.model import MembershipType

from integration.auth import AuthProvider
from integration.browser.tests.browser_test import BrowserTest
from integration.utils.constants import (
  CREATE_USER_EMAIL_SEARCH_TERM,
  OWNER_INVITE_EMAIL_SEARCH_TERM,
  VERIFY_EMAIL_SEARCH_TERM,
)
from integration.utils.emails import extract_signup_code


class TestUser(BrowserTest):
  def check_for_create_account_email(self, inbox, emails):
    inbox.wait_for_email(emails, search_term=CREATE_USER_EMAIL_SEARCH_TERM)

  def check_for_owner_invite_email(self, inbox, emails):
    inbox.wait_for_email(emails, search_term=OWNER_INVITE_EMAIL_SEARCH_TERM)

  def check_for_verify_email(self, inbox, emails):
    inbox.wait_for_email(emails, search_term=VERIFY_EMAIL_SEARCH_TERM)

  @pytest.fixture(autouse=True)
  def ensure_signup(self, config_broker):
    if config_broker.get("features.requireInvite"):
      pytest.skip()

  def fill_in_signup_form(self, page, email=None, skip_email=False, skip_client=False):
    page.locator(".signup-form [name='name']").fill(AuthProvider.randomly_generated_password())
    pwd = AuthProvider.randomly_generated_password()
    page.locator(".signup-form [name='new-password']").fill(pwd)
    if not skip_email:
      page.locator(".signup-form [name='email']").fill(email or AuthProvider.randomly_generated_email())
      if not skip_client:
        page.locator(".signup-form [name='client']").fill(AuthProvider.randomly_generated_password())

  def fill_in_setup_form(
    self,
    page,
    optimize=None,
    track=None,
  ):
    page.wait_for_selector("form.setup-form")
    if optimize:
      page.click("#optimize")
    if track:
      page.click("#track")

  def submit_setup_form(self, page):
    page.click("form.setup-form input[type='submit']")

  def submit_signup_form(self, page):
    page.click("form.signup-form input[type='submit']")

  def test_signup(self, page, inbox, routes):
    email = AuthProvider.randomly_generated_email()
    page.goto(routes.get_full_url("/signup"))
    page.wait_for_selector("text=Sign Up")
    self.fill_in_signup_form(page, email=email, skip_client=True)
    self.submit_signup_form(page)
    page.wait_for_selector(".thanks-message")
    assert "Thanks for signing up!" in page.text_content(".thanks-message")
    self.check_for_verify_email(inbox, email)

  def test_signup_with_code(self, page, api_connection, inbox, routes):
    email = AuthProvider.randomly_generated_email()
    api_connection.clients(api_connection.client_id).invites().create(email=email, role=ADMIN_ROLE, old_role=NO_ROLE)
    code = extract_signup_code(inbox, email)

    page.goto(routes.get_full_url(f"/signup?code={code}&email={email}"))
    page.wait_for_selector("[value='Sign Up']")
    self.fill_in_signup_form(page, skip_email=True)
    with page.expect_navigation(url=routes.get_full_url("/setup")):
      self.submit_signup_form(page)
    self.check_for_create_account_email(inbox, email)

  def test_signup_with_link(self, page, api_connection, inbox, routes):
    client_for_signup = api_connection.client_id
    email_local_part = AuthProvider.randomly_generated_password()
    email_domain = "example.com"

    api_connection.organizations(api_connection.organization_id).update(
      allow_signup_from_email_domains=True, client_for_email_signup=client_for_signup, email_domains=[email_domain]
    )

    token = api_connection.clients(client_for_signup).tokens().create()
    page.goto(routes.get_full_url(f"/signup?token={token.token}"))
    page.wait_for_selector("[value='Sign Up']")
    self.fill_in_signup_form(page, email=email_local_part, skip_client=True)
    self.submit_signup_form(page)
    assert "Thanks for signing up!" in page.text_content(".thanks-message")
    self.check_for_verify_email(inbox, f"{email_local_part}@{email_domain}")

  def test_first_login(self, logged_in_page, routes):
    logged_in_page.goto(routes.get_full_url("/setup"))
    self.fill_in_setup_form(logged_in_page, True, True)
    with logged_in_page.expect_navigation(url="/home"):
      self.submit_setup_form(logged_in_page)
    logged_in_page.is_hidden(".spinner")
    logged_in_page.wait_for_selector("text=Home")

  def test_first_login_skip(self, logged_in_page, routes):
    logged_in_page.goto(routes.get_full_url("/setup"))
    self.fill_in_setup_form(logged_in_page, True, False)
    logged_in_page.click("text=Skip")
    logged_in_page.is_hidden(".spinner")
    logged_in_page.wait_for_selector("text=Home")

  def test_guest_signup(self, page, api_connection, inbox, routes):
    with api_connection.create_any_experiment() as e:
      guest_token = api_connection.experiments(e.id).tokens().create().token
      guest_url = "/guest?guest_token=" + guest_token
      page.goto(routes.get_full_url(guest_url))

    email = AuthProvider.randomly_generated_email()
    api_connection.clients(api_connection.client_id).invites().create(email=email, role=ADMIN_ROLE, old_role=NO_ROLE)
    code = extract_signup_code(inbox, email)
    page.goto(routes.get_full_url(f"/signup?code={code}&email={email}"))
    self.fill_in_signup_form(page, skip_email=True)
    self.submit_signup_form(page)
    self.check_for_create_account_email(inbox, email)

  def test_owner_signup_with_code(self, page, api_connection, inbox, routes):
    email = AuthProvider.randomly_generated_email()
    api_connection.organizations(api_connection.organization_id).invites().create(
      email=email, client_invites=[], membership_type=MembershipType.owner.value
    )
    code = extract_signup_code(inbox, email)

    page.goto(routes.get_full_url(f"/signup?code={code}&email={email}"))
    page.wait_for_selector("text=Sign Up")
    self.fill_in_signup_form(page, skip_email=True)
    with page.expect_navigation(url=routes.get_full_url("/setup")):
      self.submit_signup_form(page)
    self.check_for_owner_invite_email(inbox, email)

  def test_someone_elses_code(self, logged_in_page, api_connection, inbox, routes):
    email = AuthProvider.randomly_generated_email()
    logged_in_page.goto(routes.get_full_url(f"/signup?code=someothercode&email={email}"))
    assert "invite has expired, or is not for you" in logged_in_page.text_content(".signup-description.invalid-invite")
    assert len(inbox.check_email(email)) == 0


class TestChangePassword(BrowserTest):
  @pytest.fixture(autouse=True)
  def load_page(self, logged_in_driver):
    logged_in_driver.get_path("/change_password")
    logged_in_driver.find_clickable(css_selector='input[value="Update"]')

  def test_change_password(self, logged_in_driver, login_state):
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="old-password"]',
      keys=login_state.password,
    )
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="new-password"]',
      keys=login_state.password + "1",
    )
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="verify-password"]',
      keys=login_state.password + "1",
    )
    logged_in_driver.find_and_click(css_selector='input[value="Update"]')
    logged_in_driver.wait_for_path("/user/info")

    logged_in_driver.get_path("/tokens/info")
    logged_in_driver.wait_for_element_by_css_selector('input[name="client-id"]')
    client_id = logged_in_driver.find_element_by_css_selector("input[name='client-id']").get_attribute("value")
    assert client_id == login_state.client_id
    client_token = logged_in_driver.find_element_by_css_selector("input[name='api-token']").get_attribute("value")
    assert client_token != login_state.client_token

  def test_verify_password(self, logged_in_driver, login_state):
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="old-password"]', keys=login_state.password
    )
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="new-password"]', keys=login_state.password
    )
    logged_in_driver.find_and_send_keys(
      css_selector='.change-password-form [name="verify-password"]', keys="something else"
    )
    logged_in_driver.find_and_click(css_selector='input[value="Update"]')
    logged_in_driver.find_element_by_text("Passwords must match.")


class TestMultipleClients(BrowserTest):
  def test_async_delete_and_create_client(self, logged_in_driver, api_connection, login_state):
    driver = logged_in_driver

    api_connection.clients(login_state.client_id).delete()
    driver.get_path("/user/info", title_text="My Profile - SigOpt", wait_time=5)
    driver.wait_for_element_by_css_selector(".alert-danger")
    driver.wait_while_present(css_selector='.nav-link[href="/tokens/info"]')

    api_connection.clients().create(name="Test client")
    driver.get_path("/user/info", title_text="My Profile - SigOpt", wait_time=5)
    driver.wait_for_element_by_css_selector('.nav-link[href="/tokens/info"]')

  def test_sync_delete_client(self, logged_in_driver, api_connection, login_state):
    driver = logged_in_driver

    api_connection.clients().create(name="Other Client")

    client = api_connection.clients(login_state.client_id).fetch()
    driver.get_path(f"/client/{login_state.client_id}/delete")
    driver.find_and_click(css_selector=f"input[value='Delete {client.name}']")

    driver.wait_for_path("/user/info")
    driver.wait_for_element_by_text("My Profile")

  def test_switch_client(self, logged_in_driver, api_connection):
    driver = logged_in_driver
    org_id = int(api_connection.organization_id)
    api_connection.organizations(org_id).clients().create(name="Other Client")

    driver.get_path("/user/info")

    driver.find_and_click(css_selector="#accordion-header")
    driver.wait_for_element_by_css_selector(css_selector='#accordion-links[data-open-accordion="true"]')
    accordion_client_name = driver.find_elements_by_css_selector('#accordion-links [data-type="team"] p')[0].text
    assert accordion_client_name != "Other Client"
    driver.find_and_click(element_text="Other Client")

    driver.wait_for_element_by_css_selector(css_selector='#accordion-links[data-open-accordion="false"]')
    sleep(2)
    driver.find_and_click(css_selector="#accordion-header .nav-link")
    driver.wait_for_element_by_css_selector(css_selector='#accordion-links[data-open-accordion="true"]')
    accordion_client_name = driver.find_elements_by_css_selector('#accordion-links [data-type="team"] p')[0].text
    assert accordion_client_name == "Other Client"
