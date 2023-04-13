# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64

from zigopt.profile.timing import *
from zigopt.queue.message import BaseMessageBody, QueueMessage, ReceivedMessage


def log_message_content(message_content):
  if isinstance(message_content, str):
    message_content = message_content.encode()
  return base64.b64encode(message_content).decode("ascii")


class QueueWorker:
  # To be defined by subclasses
  MESSAGE_TYPE: str  # defined by MessageType
  MessageBody: BaseMessageBody

  def __init__(self, services, message):
    assert isinstance(message, (QueueMessage, ReceivedMessage))
    assert message.message_type == self.MESSAGE_TYPE
    self.services = services
    self.message = message

  @property
  def enqueue_time(self):
    if isinstance(self.message, ReceivedMessage):
      return self.message.enqueue_time
    return None

  @time_function(
    "sigopt.queue.workers.timing",
    log_attributes=lambda self: {
      "message_content": log_message_content(self.message.serialized_body),
      "message_class": type(self.message.deserialized_message).__name__,
    },
  )
  def handle(self):
    return self._handle_message(self.message.deserialized_message)

  def _handle_message(self, message):
    raise NotImplementedError
