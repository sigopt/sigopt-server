# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import dataclasses
import email
import email.mime
import email.mime.multipart
import email.mime.text
import smtplib
from contextlib import contextmanager

from zigopt.services.base import Service


@dataclasses.dataclass
class SmtpConnectionInfo:
  host: str
  port: int
  username: str | None
  password: str | None
  tls: str | None


class SmtpEmailService(Service):
  def __init__(self, services):
    super().__init__(services)
    self.enabled = self.services.config_broker.get_bool("smtp.enabled", default=False)
    self.connection_info = None
    if self.enabled:
      self.connection_info = SmtpConnectionInfo(
        host=self.services.config_broker.get_string("smtp.host"),
        port=self.services.config_broker.get_int("smtp.port"),
        username=self.services.config_broker.get_string("smtp.username", default=None),
        password=self.services.config_broker.get_string("smtp.password", default=None),
        tls=self.services.config_broker.get_bool("smtp.tls", default=False),
      )
    self.timeout = self.services.config_broker.get_int("smtp.timeout", default=10)
    self.smtp = None

  @contextmanager
  def _make_connection(self):
    if not self.enabled or self.connection_info is None:
      raise Exception("SMTP service not enabled")
    smtp = smtplib.SMTP(timeout=self.timeout)
    smtp.connect(host=self.connection_info.host, port=self.connection_info.port)
    if self.connection_info.tls:
      smtp.starttls()
    if self.connection_info.username and self.connection_info.password:
      smtp.login(self.connection_info.username, self.connection_info.password)
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
