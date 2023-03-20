# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.optimize.worker import ExperimentWorker
from zigopt.protobuf.gen.queue.messages_pb2 import ImportancesMessage
from zigopt.queue.message import ProtobufMessageBody
from zigopt.queue.message_types import MessageType


class ImportancesWorker(ExperimentWorker):
  MESSAGE_TYPE = MessageType.IMPORTANCES

  class MessageBody(ProtobufMessageBody):
    PROTOBUF_CLASS = ImportancesMessage

  def process(self, experiment, message):
    return self.services.importances_service.compute_parameter_importances(experiment)
