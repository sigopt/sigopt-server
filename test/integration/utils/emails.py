# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from urllib.parse import parse_qs, urlparse

from integration.utils.html import validate_html


def _find_code_from_link(inbox, email, path):
  message_bodies = inbox.wait_for_email(email, search_term=f"{path}?")
  for text in reversed(message_bodies):
    parsed = validate_html(text)
    # iterdescendants by tag broke with lxml 4.9.1
    for tag in parsed.iterdescendants():
      if tag.tag != "a":
        continue
      link = tag.attrib["href"]
      parsed_link = urlparse(link)
      if parsed_link.path == path:
        params = parse_qs(parsed_link.query)
        (code,) = params["code"]
        assert code
        return code
  raise Exception(f"Could not find a {path} link in email messages for {email}")


def extract_verify_code(inbox, email):
  return _find_code_from_link(inbox, email, "/verify")


def extract_signup_code(inbox, email):
  return _find_code_from_link(inbox, email, "/signup")


def extract_password_reset_code(inbox, email):
  return _find_code_from_link(inbox, email, "/change_password")
