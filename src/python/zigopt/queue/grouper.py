# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.lib import copy_protobuf
from zigopt.services.base import Service


DIVIDER = ":"


class MessageGrouper:
  def validate_unpersisted_deserialized_message(self, deserialized_message, group_key):
    self.parse_group_key(group_key)
    self.apply_to_deserialized_message(copy_protobuf(deserialized_message), group_key)

  def parse_group_key(self, group_key):
    raise NotImplementedError()

  def unparse_deserialized_message(self, deserialized_message):
    raise NotImplementedError()

  def apply_to_deserialized_message(self, deserialized_message, group_key):
    raise NotImplementedError()


class ExperimentGrouper(MessageGrouper):
  def unparse_deserialized_message(self, deserialized_message):
    return f"{deserialized_message.experiment_id}"

  def parse_group_key(self, group_key):
    return int(group_key)

  def apply_to_deserialized_message(self, deserialized_message, group_key):
    experiment_id = self.parse_group_key(group_key)
    deserialized_message.experiment_id = experiment_id


class QueueMessageGrouper(Service):
  def __init__(self, services):
    super().__init__(services)
    self.grouper = ExperimentGrouper()

  def group_key_for_queue_message(self, queue_message):
    deserialized_message = queue_message.deserialized_message
    return self.grouper.unparse_deserialized_message(deserialized_message)

  def validate_unpersisted_deserialized_message(self, deserialized_message, group_key):
    return self.grouper.validate_unpersisted_deserialized_message(deserialized_message, group_key)

  def apply_to_deserialized_message(self, deserialized_message, group_key):
    return self.grouper.apply_to_deserialized_message(deserialized_message, group_key)
