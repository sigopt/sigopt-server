# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import email
import email.mime
import email.mime.multipart
import email.mime.text
import smtplib
from contextlib import contextmanager

from zigopt.services.base import Service


class SmtpEmailService(Service):
  def __init__(self, services):
    super().__init__(services)
    self.enabled = self.services.config_broker.get_bool("smtp.enabled", default=False)
    self.host = self.services.config_broker.get_string("smtp.host", default=None)
    self.port = self.services.config_broker.get_int("smtp.port", default=None)
    self.port = int(self.port) if self.port else self.port
    self.username = self.services.config_broker.get_string("smtp.username", default=None)
    self.password = self.services.config_broker.get_string("smtp.password", default=None)
    self.tls = self.services.config_broker.get_bool("smtp.tls", default=False)
    self.timeout = self.services.config_broker.get_int("smtp.timeout", default=10)
    self.smtp = None

  @contextmanager
  def _make_connection(self):
    smtp = smtplib.SMTP(timeout=self.timeout)
    smtp.connect(host=self.host, port=self.port)
    if self.tls:
      smtp.starttls()
    if self.username and self.password:
      smtp.login(self.username, self.password)
    yield smtp
    smtp.quit()

  def test_connection(self):
    if self.enabled:
      with self._make_connection() as smtp:
        status, message = smtp.noop()
      if status != 250:
        raise Exception(
          f"SMTP is enabled but failed to connect to SMTP server! Received status {status}, message {message}",
        )

  def send(self, message):
    msg_root = email.mime.multipart.MIMEMultipart("related")
    msg_text = email.mime.text.MIMEText(message.body_html, "html", "utf-8")
    msg_root.attach(msg_text)

    msg_root["Subject"] = message.subject
    msg_root["From"] = message.from_address
    msg_root["To"] = ", ".join(message.to)

    with self._make_connection() as smtp:
      smtp.sendmail(message.from_address, message.to, msg_root.as_string())
