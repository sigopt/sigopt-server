# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.protobuf.gen.test.message_pb2 import Child
from zigopt.queue.message import ProtobufMessageBody, QueueMessage


def test_protobuf_queue_message():
  class TestProtobufMessageBody(ProtobufMessageBody):
    PROTOBUF_CLASS = Child

  protobuf = Child(
    value=1.0,
    name="abc",
  )
  message = QueueMessage("message-type", TestProtobufMessageBody(protobuf))
  assert message.message_type == "message-type"
  assert message.deserialized_message == protobuf
  assert message.serialized_body == protobuf.SerializeToString()
