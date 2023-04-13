# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import os

import pytest
from playwright.sync_api import sync_playwright

from zigopt.common import *
from zigopt.fs.dir import ensure_dir

from integration.base import BaseTest
from integration.browser.web_driver import SigOptWebDriver
from integration.web.test_base import Routes


SELENIUM_CRITICAL_LEVELS = ["SEVERE", "ERROR", "CRITICAL"]
PLAYWRIGHT_CRITICAL_LEVELS = ["error"]


def sanitize_test_name_for_path(test_name):
  return "".join([c if c.isalnum() else "_" for c in test_name])


def audit_console_logs(logs, critical_levels):
  errors = []
  for log in logs:
    message = log["message"]
    ignored_messages = [
      "Lost DOM in window undefined",
      "Failed to load resource: the server responded with a status of",
      "This is a test error, no cause for alarm",
      "chrome-extension://invalid/ - Failed to load resource: net::ERR_FAILED",
      "Warning: componentWillMount has been renamed, and is not recommended for use.",
      "Warning: Legacy context API has been detected within a strict-mode tree.",
      "Warning: componentWillReceiveProps has been renamed, and is not recommended for use.",
      "Learn more about using refs safely here: https://fb.me/react-strict-mode-find-node",
      "does not specify a 'report-uri'",
      " has been blocked by CORS policy",
      "Failed to load resource: net::ERR_FAILED",
    ]
    if log["level"] in critical_levels and not any(ignored_message in message for ignored_message in ignored_messages):
      errors.append(f'[{log["level"]}] {log["message"]}')
  return errors


def capture_page_logs(page):
  logs = []
  page.on(
    "console",
    lambda message: logs.append(
      {
        "level": message.type,
        "message": message.text,
      }
    ),
  )
  return logs


def save_console_logs(test, logs):
  CONSOLE_LOG_DIR = "failure_console_logs"
  ensure_dir(CONSOLE_LOG_DIR)
  sanitized_name = sanitize_test_name_for_path(test.name)
  f = os.path.join(CONSOLE_LOG_DIR, f"{sanitized_name}.txt")
  if logs:
    with open(f, "w", encoding="utf-8") as outfile:
      for entry in logs:
        outfile.write(f"{json.dumps(entry)}\n")


def failure_screenshot(test, save):
  dirname = os.path.join("screenshots", "failure")
  ensure_dir(dirname)
  sanitized_name = sanitize_test_name_for_path(test.name)
  save(os.path.join(dirname, f"{sanitized_name}.png"))


def cleanup_test(test, get_logs, critical_log_levels, save_screenshot):
  logs = get_logs()
  errors = audit_console_logs(logs, critical_log_levels)
  if errors or getattr(test, "failed", False):
    save_console_logs(test, logs)
    failure_screenshot(test, save_screenshot)
  if errors:
    pytest.fail("\n".join(errors))


# This hook is used to detect if the test failed within the fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
  # execute all other hooks to obtain the report object
  outcome = yield
  rep = outcome.get_result()
  # set an report attribute for each phase of a call, which can
  # be "setup", "call", "teardown"
  setattr(item, "failed", rep.failed or getattr(rep, "failed", False))


@pytest.fixture(name="browser", scope="session")
def fixture_browser(config_broker):
  return config_broker["test.browser"]


@pytest.fixture(name="headless", scope="session")
def fixture_headless(request):
  return request.param


@pytest.fixture(scope="session")
def _session_driver(browser, headless, config_broker):
  # NOTE: This fixture creates the web driver at the session scope,
  # but individual tests should use the test-scoped fixtures below, because
  # they will correctly save screenshots/logs for each test
  driver = SigOptWebDriver(
    driver_name=browser,
    app_url=BaseTest.get_app_url(config_broker),
    config_broker=config_broker,
    headless=headless,
  )
  yield driver
  driver.close()


@pytest.fixture(scope="function")
def _driver(request, _session_driver):
  yield _session_driver
  cleanup_test(request.node, _session_driver.get_logs, SELENIUM_CRITICAL_LEVELS, _session_driver.save_screenshot)


# TODO(SN-970): firefox and webkit button clicks are flaky, why?
@pytest.fixture(name="playwright_browser", scope="session", params=["chrome"])
def fixture_playwright_browser(headless, config_broker, request):
  kwargs = {"headless": headless}
  if request.param == "chrome":
    browser = "chromium"
    kwargs["channel"] = "chrome"
  else:
    browser = request.param
  with sync_playwright() as p:
    yield getattr(p, browser).launch(**kwargs)


@pytest.fixture(name="playwright_page", scope="function")
def fixture_playwright_page(request, playwright_browser):
  browser = playwright_browser
  width, height = (int(x) for x in os.environ.get("GEOMETRY", "1920x1080").split("x"))
  context = browser.new_context(ignore_https_errors=True, viewport={"width": width, "height": height})
  page = context.new_page()
  logs = capture_page_logs(page)
  yield page
  try:
    cleanup_test(request.node, lambda: logs, PLAYWRIGHT_CRITICAL_LEVELS, lambda path: page.screenshot(path=path))
  finally:
    page.close()


@pytest.fixture(name="driver", scope="function")
def fixture_driver(request, _driver, web, api):
  _driver.reset()
  yield _driver


@pytest.fixture(name="page", scope="function")
def fixture_page(playwright_page, web, api):
  yield playwright_page


def log_in_driver(driver, web_connection, login_state=None):
  driver.reset()
  if login_state is not None:
    web_connection.email = login_state.email
    web_connection.password = login_state.password
  driver.web_connection = web_connection
  driver.login()
  return driver


@pytest.fixture(scope="function")
def logged_in_driver(_driver, web, web_connection, login_state):
  return log_in_driver(_driver, web_connection, login_state)


def log_in_page(page, config_broker, web_connection, login_state=None):
  if login_state is not None:
    web_connection.email = login_state.email
    web_connection.password = login_state.password
  web_connection.login()
  page.context.add_cookies(web_connection.get_browser_cookies(config_broker))
  return page


@pytest.fixture(scope="function")
def logged_in_page(playwright_page, web_connection, login_state, config_broker, web, api):
  return log_in_page(
    playwright_page,
    config_broker,
    web_connection,
    login_state,
  )


@pytest.fixture(scope="session")
def routes(app_url):
  return Routes(app_url)


def pytest_generate_tests(metafunc):
  if "headless" in metafunc.fixturenames:
    headless = getattr(metafunc.config.option, "headless", False)
    metafunc.parametrize("headless", [headless], indirect=True, scope="session")


def pytest_addoption(parser):
  parser.addoption(
    "--headless",
    action="store_true",
    help="Flag indicating browsers should run headless",
  )
