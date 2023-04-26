# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import collections
import email
import json
import logging
import threading
from email.contentmanager import ContentManager, get_text_content  # type: ignore
from email.message import EmailMessage
from email.policy import EmailPolicy

import flask
from aiosmtpd.controller import Controller

from integration.utils.mail.validate_email import validate_email


custom_content_manager = ContentManager()


def get_multipart(msg):
  assert msg.is_multipart()
  text_parts = []
  data = msg.get_payload()
  content_type = None
  for part in data:
    ct = part.get_content_type()
    assert ct.split("/")[0] == "text", "Only text/* content type supported for multipart"
    if content_type is None:
      content_type = ct
    else:
      assert ct == content_type
    text_parts.append(get_text_content(part))
  assert content_type is not None
  text = "".join(text_parts)
  validate_email(content_type, text)
  return text


custom_content_manager.add_get_handler("multipart/related", get_multipart)


class CustomEmailPolicy(EmailPolicy):
  content_manager = custom_content_manager


class _FlaskThread(threading.Thread):
  def __init__(self, server, port):
    threading.Thread.__init__(self)
    self.server = server
    self.port = port

  def run(self):
    self.server.run(host="0.0.0.0", port=self.port)


class _MailController:
  logger = logging.getLogger("sigopt.smtp_server.controller")

  def __init__(self):
    self.messages = collections.defaultdict(list)
    self.lock = threading.Lock()
    self.policy = CustomEmailPolicy()

  def add_messages(self, rcpttos, message):
    self.logger.debug("adding message")
    data = email.message_from_string(message, EmailMessage, policy=self.policy)
    self.logger.info("mail recieved: %s", data.as_string())
    with self.lock:
      for addr in rcpttos:
        self.logger.info("sending to inbox %s", addr)
        self.messages[addr.lower()].append(data)

  def list_messages(self, address):
    self.logger.debug("listing messages")
    with self.lock:
      return list(self.messages[address.lower()])

  def reset(self):
    self.logger.debug("resetting inboxes")
    with self.lock:
      self.messages.clear()


def _prepare_flask_mail_reader(mail_controller, log_level):
  reader = flask.Flask(__name__)
  logger = logging.getLogger("sigopt.smtp_server.reader")
  logger.setLevel(log_level)

  def message_to_json_data(message):
    if message:
      text = message.get_content()
      message = dict(
        body="".join(text),
      )
    return dict(message=message)

  def list_messages(address):
    logger.debug("responding to read request for %s", address)
    messages = mail_controller.list_messages(address)
    return json.dumps([message_to_json_data(message) for message in messages])

  def reset():
    logger.debug("resetting mail")
    mail_controller.reset()
    return ""

  def health():
    logger.debug("health request")
    return ""

  reader.route("/message/<address>/list", methods=["GET"])(list_messages)
  reader.route("/reset", methods=["POST"])(reset)
  reader.route("/health", methods=["GET"])(health)

  return reader


class _MessageHandler(_MailController):
  def __init__(self):
    super().__init__()
    self.parser = email.parser.Parser()  # type: ignore

  async def handle_DATA(self, server, session, envelope):
    self.add_messages(envelope.rcpt_tos, envelope.content.decode("utf-8"))
    return "250 Message accepted for delivery"


def _prepare(send_port, receive_port, verbose):
  log_level = logging.DEBUG if verbose else logging.WARNING
  mail = _MessageHandler()
  mail.logger.setLevel(log_level)
  reader = _prepare_flask_mail_reader(mail, log_level)

  mail_controller = Controller(mail, hostname="0.0.0.0", port=int(send_port))
  message_thread = _FlaskThread(reader, int(receive_port))
  message_thread.daemon = True

  return message_thread, mail_controller


def smtp_server(send_port, receive_port, verbose):
  message_thread, mail_controller = _prepare(send_port, receive_port, verbose)

  message_thread.start()

  mail_controller.start()

  message_thread.join()
