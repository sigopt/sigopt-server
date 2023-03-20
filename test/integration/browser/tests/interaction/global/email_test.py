# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.browser.tests.browser_test import BrowserTest
from integration.utils.emails import extract_verify_code


class VerifyEmailTest(BrowserTest):
  def assert_verified(self, api_connection, is_verified):
    user = api_connection.users(api_connection.user_id).fetch()
    assert user.email is not None
    assert user.has_verified_email == is_verified

  def get_email_verify_code(self, api_connection, email, inbox):
    api_connection.users(api_connection.user_id).verifications().create()
    return extract_verify_code(inbox, email)

  def verify_email(self, code, email, driver):
    driver.get_path(f"/verify?code={code}&email={email}")
    driver.find_element_by_css_selector("title")
    driver.wait_while_present(css_selector=".spinner")

  def ensure_verified_web_login(self, driver):
    driver.wait_for_path("/setup")

  def ensure_verify_error(self, driver):
    msg = "Oops"
    driver.wait_for_element_by_text(msg, partial_match=True, wait_time=30)


class TestVerifyEmail(VerifyEmailTest):
  def test_verify_no_params(self, web_connection):
    response = web_connection.get("/verify")
    assert "Resend verification email" in response

  def test_verify_email_logged_out(self, api_connection, login_state, inbox, driver):
    email = login_state.email
    code = self.get_email_verify_code(api_connection, email, inbox)
    self.verify_email(code, email, driver)
    self.ensure_verified_web_login(driver)
    self.assert_verified(api_connection, True)

  def test_verify_email_logged_in(self, logged_in_web_connection, inbox, api_connection, driver):
    email = logged_in_web_connection.email
    code = self.get_email_verify_code(api_connection, email, inbox)
    self.verify_email(code, email, driver)
    self.ensure_verified_web_login(driver)
    self.assert_verified(api_connection, True)


class TestVerifyEmailFailures(VerifyEmailTest):
  def make_unverified_connection(self, auth_provider, config_broker, api, email=None):
    login_state = self.make_login_state(auth_provider, has_verified_email=False, email=email)
    api_connection = self.make_api_connection(config_broker, api, login_state)
    return api_connection

  def test_verify_email(
    self,
    inbox,
    config_broker,
    api,
    auth_provider,
    driver,
  ):
    email = auth_provider.randomly_generated_email()
    api_connection = self.make_unverified_connection(auth_provider, config_broker, api, email)
    code = self.get_email_verify_code(api_connection, email, inbox)
    self.verify_email(code, email, driver)
    self.ensure_verified_web_login(driver)
    self.assert_verified(api_connection, True)

  def test_verify_no_code(self, config_broker, auth_provider, api, web_connection):
    email = auth_provider.randomly_generated_email()
    api_connection = self.make_unverified_connection(auth_provider, config_broker, api, email=email)
    assert "Resend verification email" in web_connection.get("/verify").body_html()
    self.assert_verified(api_connection, False)

  def test_verify_invalid_code(self, config_broker, auth_provider, api, driver):
    email = auth_provider.randomly_generated_email()
    api_connection = self.make_unverified_connection(auth_provider, config_broker, api, email=email)
    self.verify_email("badcode", email, driver)
    self.ensure_verify_error(driver)
    self.assert_verified(api_connection, False)

  def test_verify_invalid_email(self, config_broker, auth_provider, api, inbox, driver):
    email = auth_provider.randomly_generated_email()
    api_connection = self.make_unverified_connection(auth_provider, config_broker, api, email=email)
    code = self.get_email_verify_code(api_connection, email, inbox)
    self.verify_email(code, "invalid@notsigopt.ninja", driver)
    self.ensure_verify_error(driver)
    self.assert_verified(api_connection, False)


class TestResendVerification(VerifyEmailTest):
  @pytest.mark.slow
  def test_resend_verification_email(
    self,
    login_state,
    inbox,
    api_connection,
    driver,
  ):
    self.assert_verified(api_connection, True)
    api_connection.users(api_connection.user_id).verifications().create()
    self.assert_verified(api_connection, False)

    first_code = self.get_email_verify_code(api_connection, login_state.email, inbox)
    second_code = self.get_email_verify_code(api_connection, login_state.email, inbox)

    self.verify_email(first_code, login_state.email, driver)
    driver.wait_for_element_by_text("Resend verification email")
    self.verify_email(second_code, login_state.email, driver)
    self.ensure_verified_web_login(driver)
    self.assert_verified(api_connection, True)
