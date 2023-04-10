# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp


class BaseMessageBody:
  @classmethod
  def from_args(cls, *args, **kwargs):
    raise NotImplementedError()

  @property
  def content(self):
    raise NotImplementedError()

  def serialize(self):
    raise NotImplementedError()

  @classmethod
  def deserialize(cls, string):
    raise NotImplementedError()


class ProtobufMessageBody(BaseMessageBody):
  # To be defined by subclasses
  # PROTOBUF_CLASS: protobuf class

  def __init__(self, pb):
    assert isinstance(pb, self.PROTOBUF_CLASS)
    self._message_pb = pb

  @classmethod
  def from_args(cls, **kwargs):
    return cls(cls.PROTOBUF_CLASS(**kwargs))

  @property
  def content(self):
    return self._message_pb

  def serialize(self):
    return self._message_pb.SerializeToString()

  @classmethod
  def deserialize(cls, string):
    pb = cls.PROTOBUF_CLASS()
    pb.ParseFromString(string)
    return cls(pb)


class QueueMessage:
  def __init__(self, message_type, message_body):
    assert isinstance(message_body, BaseMessageBody)
    self.message_type = message_type
    self.message_body = message_body

  @property
  def serialized_body(self):
    return self.message_body.serialize()

  @property
  def deserialized_message(self):
    return self.message_body.content


class ReceivedMessage:
  def __init__(self, queue_message, handle, enqueue_time, group_key=None):
    assert isinstance(queue_message, QueueMessage)
    self.queue_message = queue_message
    self.handle = handle
    self.enqueue_time = coalesce(enqueue_time, unix_timestamp())
    self.group_key = group_key

  @property
  def message_type(self):
    return self.queue_message.message_type

  @property
  def serialized_body(self):
    return self.queue_message.serialized_body

  @property
  def deserialized_message(self):
    return self.queue_message.deserialized_message
