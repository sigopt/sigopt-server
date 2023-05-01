# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.email.model import HtmlEmail
from zigopt.protobuf.gen.queue.messages_pb2 import SendEmailMessage
from zigopt.queue.message import ProtobufMessageBody
from zigopt.queue.message_groups import MessageGroup
from zigopt.queue.message_types import MessageType
from zigopt.queue.worker import QueueWorker


class EmailWorker(QueueWorker):
  MESSAGE_GROUP = MessageGroup.ANALYTICS
  MESSAGE_TYPE = MessageType.EMAIL

  class MessageBody(ProtobufMessageBody):
    PROTOBUF_CLASS = SendEmailMessage

  def _handle_message(self, message):
    msg = HtmlEmail(
      to=message.to,
      subject=message.subject,
      body_html=message.body_html,
      from_address=message.from_address,
      bypass_list_management=message.bypass_list_management,
    )
    self.services.email_router.send(msg)
