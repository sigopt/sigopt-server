# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import html
import os

from mako.template import Template

from zigopt.common import *
from zigopt.brand.constant import EMAIL_MAKO_TEMPLATE_FILE


def email_escape(val):
  return html.escape(str(val), quote=True)


TEMPLATE_CACHE: dict[frozenset, Template] = {}


def make_template(**kwargs):
  kwargs.setdefault("default_filters", ["h"])
  cache_key = frozenset([(key, tuple(value) if is_sequence(value) else value) for (key, value) in kwargs.items()])
  return TEMPLATE_CACHE.setdefault(cache_key, Template(**kwargs))


def render_email_template(path, **kwargs):
  t = make_template(filename=path)
  return t.render_unicode(**kwargs)


def create_mako_email(
  template_path,
  params,
  to,
  subject,
  from_address,
  app_url,
  base_template=None,
  bypass_list_management=False,
):
  base_template = base_template or os.path.join(os.path.dirname(__file__), EMAIL_MAKO_TEMPLATE_FILE)
  inner_template = os.path.join(os.path.dirname(__file__), template_path)
  inner_html = render_email_template(inner_template, **params)
  body_html = render_email_template(
    base_template,
    email_body=inner_html,
    app_url=app_url,
  )
  return HtmlEmail(
    to=to,
    subject=subject,
    body_html=body_html,
    from_address=from_address,
    bypass_list_management=bypass_list_management,
  )


class HtmlEmail(object):
  # bypass_list_management means that the email will be sent even if the user has unsubscribed.
  # This should be used only for necessary, user-initiated emails, such as a password reset
  def __init__(self, to, subject, body_html, from_address, bypass_list_management=False):
    if is_string(to):
      to = [to]
    self.to = to
    self.subject = subject
    self.body_html = body_html
    self.from_address = from_address
    self.bypass_list_management = bypass_list_management

  def __repr__(self):
    return (
      f'{self.__class__.__name__}: from <{self.from_address}> to <{", ".join(self.to)}>\n'
      f"{self.subject}\n"
      f"{self.body_html}"
    )
