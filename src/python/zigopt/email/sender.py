# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.email.model import HtmlEmail
from zigopt.services.base import Service


class BaseEmailService(Service):
  def should_send(self, email):
    internal_email_domains = self.services.config_broker.get("email.additional_internal_domains", [])
    return bool(
      not self.services.config_broker.get("email.internal_only")
      or all(e.endswith(tuple(internal_email_domains)) for e in email.to)
    )

  def send(self, email):
    raise NotImplementedError()


class EmailSenderService(BaseEmailService):
  def __init__(self, services):
    super().__init__(services)
    self.enabled = self.services.config_broker.get("email.enabled", default=True)
    self.method = self.services.config_broker.get("email.method", default="smtp")
    self.from_address = self.services.config_broker.get("email.from_address", default=None)
    assert self.method in ("smtp",)

  def _sanitize(self, email):
    if self.from_address:
      email.from_address = self.from_address
    return email

  def send(self, email):
    assert isinstance(email, HtmlEmail)
    email = self._sanitize(email)
    subject_prefix = self.services.config_broker.get("email.subject_prefix", "")
    email.subject = subject_prefix + email.subject
    if self.enabled and self.should_send(email):
      self.services.smtp_email_service.send(email)
    else:
      text_to_print = [email.subject, "To: " + ", ".join(email.to), "====="]
      text_to_print.append(email.body_html)
      self.services.logging_service.getLogger("sigopt.email").info(
        "Did not send the following email: %s",
        "\n".join(text_to_print),
      )
