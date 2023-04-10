# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import integration.browser.helpers.matcher as Matcher
from integration.browser.models.test_error import ErrorInTest


class TimeoutErrorInTest(ErrorInTest):
  def __init__(self, time):
    super().__init__(f"Timeout occurred in test after {time} seconds")
    self.time = time


def find_and_click(driver, element_text=None, css_selector=None, repeat=1, **kwargs):
  """
    Searches for an element on the page, ensures it is clickable, and then clicks on it
    Note: when using this function, prefer text selection over attribute selection so as to
    closer mimic how an end user would use our site
    """
  if repeat < 1:
    raise ErrorInTest(f"Repeat must be a positive integer, received: {repeat}")

  element = find_clickable(driver, element_text=element_text, css_selector=css_selector, **kwargs)
  for i in range(repeat):
    try:
      element.click()
    except StaleElementReferenceException as e:
      if css_selector:
        raise ErrorInTest(f"Element described by `{css_selector}` is stale after {i} clicks") from e
      if element_text:
        raise ErrorInTest(f"Element with text `{element_text}` is stale after {i} clicks") from e
      raise

  return element


def find_and_send_keys(driver, element_text=None, css_selector=None, keys=None, clear=False):
  element = find_clickable(
    driver,
    element_text=element_text,
    css_selector=css_selector,
  )
  if clear:
    # NOTE: We've observed `clear` not working in current versions of selenium / chrome,
    # so fallback to a bunch of backspaces
    element.send_keys(Keys.BACKSPACE * 50)
    element.clear()
  element.send_keys(keys)
  return element


def find_clickable(driver, *, element_text=None, css_selector=None, **kwargs):
  if css_selector:
    element = driver.find_element_by_css_selector(css_selector)
  elif element_text:
    element = find_element_by_text(driver, element_text=element_text)
  else:
    raise ErrorInTest("No text given to search for")

  try:
    _wait_for_clickable(driver, element=element, **kwargs)
  except TimeoutErrorInTest as e:
    if css_selector:
      raise ErrorInTest(f"Element described by `{css_selector}` was not clickable in {e.time} seconds") from e
    if element_text:
      raise ErrorInTest(f"Element with text `{element_text}` was not clickable in {e.time} seconds") from e
    raise

  return element


def wait_for(driver, method, wait_time=10):
  try:
    WebDriverWait(driver, wait_time).until(method)
  except TimeoutException as e:
    raise TimeoutErrorInTest(wait_time) from e


def wait_for_element_by_css_selector(driver, css_selector, *args, **kwargs):
  wait_for(driver, lambda s: len(s.find_elements_by_css_selector(css_selector)) > 0, *args, **kwargs)


def wait_for_element_by_xpath(driver, xpath, *args, **kwargs):
  wait_for(driver, lambda s: len(s.find_elements_by_xpath(xpath)) > 0, *args, **kwargs)


def _wait_for_clickable(driver, element, *args, **kwargs):
  """
    Extend Selenium's internal implementation of clickable to include our use of disabled `a` tags
    """
  wait_for(
    driver,
    lambda s: all((element.is_displayed(), element.is_enabled(), element.get_attribute("disabled") != "true")),
    *args,
    **kwargs,
  )


def wait_for_clickable(driver, element, *args, **kwargs):
  try:
    _wait_for_clickable(driver, element, *args, **kwargs)
  except TimeoutErrorInTest as e:
    raise ErrorInTest(f"Element given was not clickable in {e.time} seconds") from e


def find_elements_by_text(driver, element_text, partial_match=False):
  return driver.find_elements_by_xpath(Matcher.text_in_element(element_text, partial_match))


def find_element_by_text(driver, element_text, partial_match=False):
  return driver.find_element_by_xpath(Matcher.text_in_element(element_text, partial_match))


def wait_for_element_by_text(driver, element_text, partial_match=False, **kwargs):
  return driver.wait_for_element_by_xpath(Matcher.text_in_element(element_text, partial_match), **kwargs)


def set_select_option(element, option_text):
  for option in element.find_elements(By.TAG_NAME, "option"):
    if option.text == option_text:
      option.click()
      break


def wait_while_present(driver, element_text=None, css_selector=None, **kwargs):
  try:
    if css_selector:
      wait_for(driver, lambda s: len(driver.find_elements_by_css_selector(css_selector)) == 0, **kwargs)
    elif element_text:
      wait_for(driver, lambda s: len(find_elements_by_text(driver, element_text)) == 0, **kwargs)
  except TimeoutErrorInTest as e:
    if element_text is not None:
      raise ErrorInTest(f"Element with text `{element_text}` was still present in {e.time} seconds") from e
    if css_selector is not None:
      raise ErrorInTest(f"Element described by `{css_selector}` was still present in {e.time} seconds") from e
    raise


# It would be weird to search by element text here, but it's included for completeness.
def wait_for_text_in_element(driver, by, value, text, *args, **kwargs):
  try:
    wait_for(driver, EC.text_to_be_present_in_element((by, value), text), *args, **kwargs)
  except TimeoutErrorInTest as e:
    raise ErrorInTest(f"Text {text} not present in element with {by} `{value}` in {e.time} seconds") from e


def wait_for_url(driver, url, *args, **kwargs):
  try:
    # Selenium fails to recognize that http://google.com:80 == http://google.com
    wait_for(driver, lambda s: driver.current_url == url.replace(":80/", "/", 1), *args, **kwargs)
  except TimeoutErrorInTest as e:
    raise ErrorInTest(f"Waited for {url}, current url is {driver.current_url} after {e.time} seconds") from e


def wait_for_title_text(driver, title_text, *args, **kwargs):
  class our_title_contains:
    def __init__(self, title):
      self.title = title

    def __call__(self, driver):
      return self.title in driver.title or driver.title == "Leaving Hosted Site - SigOpt"

  try:
    wait_for(driver, our_title_contains(title_text), *args, **kwargs)
  except TimeoutErrorInTest as e:
    raise ErrorInTest(f"Failed to read page title after {e.time} seconds") from e
  else:
    title = driver.title
    if title == "Leaving Hosted Site - SigOpt":
      pytest.skip()
    elif title_text not in title:
      raise ErrorInTest(f"Waited for page title `{title_text}`, instead has page title `{title}`")
