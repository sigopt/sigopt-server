# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.email.sender import BaseEmailService


class EmailRouterService(BaseEmailService):
  def __init__(self, services, is_qworker):
    super().__init__(services)
    self.is_qworker = is_qworker

  def send(self, email):
    if not self.is_qworker and self.services.config_broker.get("email.queue", True):
      self.services.email_queue_service.send(email)
    else:
      self.services.immediate_email_sender.send(email)
