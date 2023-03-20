# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import os
import socket
import warnings
from urllib.error import URLError

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

from zigopt.common import *
from zigopt.fs.dir import ensure_dir

from integration.browser.helpers import navigation_helper
from integration.browser.models.test_error import FindElementErrorInTest
from integration.web.test_base import Routes


LOGGING_PREFS = {"browser": "ALL"}


class CustomChromeOptions(webdriver.ChromeOptions):
  @property
  def default_capabilities(self):
    d = super().default_capabilities
    d["goog:loggingPrefs"] = LOGGING_PREFS
    return d


class SigOptWebDriver(object):
  def __getattr__(self, name):
    if name.endswith("_by_class_name"):
      warnings.warn(
        f"{name} may no longer work as expected, prefer *_by_css_selector methods",
        UserWarning,
      )
    func = getattr(self.driver, name)
    if callable(func):

      def safety_wrapper(*args, **kwargs):
        try:
          return func(*args, **kwargs)
        except NoSuchElementException as e:
          raise FindElementErrorInTest(e) from e

      return safety_wrapper
    else:
      return func

  def __init__(self, driver_name, app_url, config_broker, headless=False):
    self.driver_name = driver_name
    self.app_url = app_url
    self.routes = Routes(app_url)
    self.config_broker = config_broker
    self.web_connection = None
    chrome_options = CustomChromeOptions()
    chrome_options.add_argument("disable-extensions")
    chrome_options.add_argument("ignore-certificate-errors")
    if headless:
      chrome_options.add_argument("headless")
    chrome_options.add_argument("no-sandbox")
    if driver_name == "Chrome":
      self.driver = webdriver.Chrome(options=chrome_options)
    elif driver_name == "Firefox":
      d = DesiredCapabilities.FIREFOX
      options = webdriver.FirefoxOptions()
      if headless:
        options.add_argument("-headless")
      self.driver = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(), capabilities=d, options=options)
    elif driver_name.startswith("Remote:"):
      _, driver_name, *address = driver_name.split(":")
      if len(address) == 0:
        address = [4444]
      if len(address) == 1:
        (port,) = address
        address = ["127.0.0.1", port]
      host, port = address
      command_executor = f"http://{host}:{port}/wd/hub"
      if driver_name == "Chrome":
        d = chrome_options.to_capabilities()
      elif driver_name == "Firefox":
        d = DesiredCapabilities.FIREFOX
      else:
        d = {}
      d["acceptInsecureCerts"] = True
      self.driver = webdriver.Remote(command_executor, options=d)
    else:
      raise Exception(f"Driver name not recognized: {self.driver_name}")
    self.driver.set_window_size(1200, 8000)
    self.get_path(title_text="")

  def get_path(self, path="", title_text=None, css_selector=None, *args, **kwargs):
    if not path.startswith("http"):
      path = self.routes.get_url_base(path) + path
    self.driver.get(path)
    if title_text is not None:
      navigation_helper.wait_for_title_text(self, title_text, *args, **kwargs)
    if css_selector is not None:
      navigation_helper.wait_for_element_by_css_selector(self, css_selector, *args, **kwargs)
    self.wait_for_page_load()
    return self

  def save_screenshot(self, path):
    dirname = os.path.dirname(path)
    try:
      ensure_dir(dirname)
      try:
        self.driver.save_screenshot(path)
      except AttributeError as e:
        if "'NoneType' object has no attribute 'encode'" in str(e):
          logging.error("Could not save image for %s", path)
        else:
          raise
    except URLError:
      # This is so that if you Ctrl-C to cancel tests, you still get
      # the test results
      pass

  def get_logs(self):
    logs = []
    try:
      logs = flatten([self.driver.get_log(t) for t in self.driver.log_types])
    except socket.error:
      # This is so that if you Ctrl-C to cancel tests, you still get
      # the test results
      pass
    return logs

  def reset(self):
    if self.web_connection:
      self.web_connection.reset()
    self.driver.delete_all_cookies()

  def login(self):
    self.web_connection.login()
    for cookie in self.web_connection.get_browser_cookies(self.config_broker):
      self.driver.add_cookie(cookie)

  def find_and_click(self, *args, **kwargs):
    results = navigation_helper.find_and_click(self, *args, **kwargs)
    return results

  def find_clickable(self, *args, **kwargs):
    results = navigation_helper.find_clickable(self, *args, **kwargs)
    return results

  def find_and_send_keys(self, *args, **kwargs):
    result = navigation_helper.find_and_send_keys(self, *args, **kwargs)
    return result

  def set_select_option(self, *args, **kwargs):
    navigation_helper.set_select_option(*args, **kwargs)
    return self

  def wait_for(self, *args, **kwargs):
    navigation_helper.wait_for(self, *args, **kwargs)
    return self

  def wait_for_clickable(self, *args, **kwargs):
    navigation_helper.wait_for_clickable(self, *args, **kwargs)
    return self

  def wait_for_element_by_css_selector(self, *args, **kwargs):
    navigation_helper.wait_for_element_by_css_selector(self, *args, **kwargs)
    return self

  def wait_for_element_by_xpath(self, *args, **kwargs):
    navigation_helper.wait_for_element_by_xpath(self, *args, **kwargs)
    return self

  def wait_for_element_by_text(self, *args, **kwargs):
    navigation_helper.wait_for_element_by_text(self, *args, **kwargs)

  def wait_for_title_text(self, *args, **kwargs):
    navigation_helper.wait_for_title_text(self, *args, **kwargs)
    return self

  def wait_for_text_in_element(self, *args, **kwargs):
    navigation_helper.wait_for_text_in_element(self, *args, **kwargs)
    return self

  def wait_while_present(self, *args, **kwargs):
    navigation_helper.wait_while_present(self, *args, **kwargs)
    return self

  def wait_for_path(self, path, *args, **kwargs):
    navigation_helper.wait_for_url(self, self.routes.get_url_base(path) + path, *args, **kwargs)
    return self

  def find_element_by_id(self, *args, **kwargs):
    return self.find_element(By.ID, *args, **kwargs)

  def find_element_by_text(self, *args, **kwargs):
    results = navigation_helper.find_element_by_text(self, *args, **kwargs)
    return results

  def find_element_by_xpath(self, *args, **kwargs):
    return self.find_element(By.XPATH, *args, **kwargs)

  def find_elements_by_xpath(self, *args, **kwargs):
    return self.find_elements(By.XPATH, *args, **kwargs)

  def find_element_by_css_selector(self, css_selector, **kwargs):
    return self.find_element(By.CSS_SELECTOR, css_selector, **kwargs)

  def find_elements_by_css_selector(self, css_selector, **kwargs):
    return self.find_elements(By.CSS_SELECTOR, css_selector, **kwargs)

  def find_element_by_link_text(self, *args, **kwargs):
    return self.find_element(By.LINK_TEXT, *args, **kwargs)

  def find_element_by_partial_link_text(self, *args, **kwargs):
    return self.find_element(By.PARTIAL_LINK_TEXT, *args, **kwargs)

  def wait_for_page_load(self, wait_time=5):
    WebDriverWait(self.driver, wait_time).until(lambda s: s.execute_script("return document.readyState") == "complete")

  def close(self):
    self.driver.quit()
