# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.browser_test import BrowserTest


class TestLogin(BrowserTest):
  def test_login_page(self, driver, login_state):
    driver.get_path("/login")
    email = login_state.email
    password = login_state.password
    driver.find_and_send_keys(css_selector=".login-form [name='email']", keys=email)
    password_input = driver.find_and_send_keys(css_selector=".login-form [name='password']", keys=password)
    password_input.submit()
    driver.wait_for_path("/home")

  def test_login_page_failure(self, page, login_state, routes):
    page.goto(routes.get_full_url("/login"))
    email = login_state.email
    page.locator(".login-form [name='email']").fill(email)
    page.locator(".login-form [name='password']").fill("wrongpass")
    page.click(".login-form input[type='submit']")
    assert "Invalid username" in page.locator(".alert-danger").inner_text()
    page.click(".alert-danger .close")
    page.is_hidden(".alert-danger")


class TestNeedsLogin(BrowserTest):
  def test_prompts_for_login(self, driver):
    driver.get_path("/user/info")
    driver.find_clickable(css_selector=".login-form")
