# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.email.sender import BaseEmailService
from zigopt.queue.message_types import MessageType


class EmailQueueService(BaseEmailService):
  def send(self, email):
    if not self.should_send(email):
      return
    with self.services.exception_logger.tolerate_exceptions(
      Exception,
      extra={
        "email_to": email and email.to,
        "email_from": email and email.from_address,
        "email_subject": email and email.subject,
      },
    ):
      self.services.queue_service.make_and_enqueue_message(
        MessageType.EMAIL,
        to=email.to,
        from_address=email.from_address,
        subject=email.subject,
        body_html=email.body_html,
        bypass_list_management=email.bypass_list_management,
      )
