# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.email.worker import EmailWorker
from zigopt.importance.worker import ImportancesWorker
from zigopt.optimize.worker import HyperparameterOptimizationWorker, NextPointsWorker
from zigopt.queue.message import QueueMessage
from zigopt.queue.message_groups import MessageGroup
from zigopt.queue.worker import QueueWorker
from zigopt.services.base import GlobalService


WORKER_CLASSES = [
  EmailWorker,
  HyperparameterOptimizationWorker,
  ImportancesWorker,
  NextPointsWorker,
]

WORKER_CLASSES_BY_MESSAGE_TYPE: dict[str, type[QueueWorker]] = {}


def assign_worker_classes_by_message_type():
  for WorkerClass in WORKER_CLASSES:
    assert WorkerClass.MESSAGE_TYPE not in WORKER_CLASSES_BY_MESSAGE_TYPE, (
      f"Worker class {WorkerClass.__name__} has a conflicting message type with"
      f" {WORKER_CLASSES_BY_MESSAGE_TYPE[WorkerClass.MESSAGE_TYPE].__name__}: {WorkerClass.MESSAGE_TYPE}"
    )
    WORKER_CLASSES_BY_MESSAGE_TYPE[WorkerClass.MESSAGE_TYPE] = WorkerClass


assign_worker_classes_by_message_type()


class MessageRouter(GlobalService):
  @classmethod
  def get_worker_class_for_message(cls, message_type):
    return WORKER_CLASSES_BY_MESSAGE_TYPE.get(message_type)

  @classmethod
  def deserialize_message(cls, message_type, serialized_body):
    if WorkerClass := cls.get_worker_class_for_message(message_type):
      message_body = WorkerClass.MessageBody.deserialize(serialized_body)
      return QueueMessage(message_type, message_body)
    return None

  @classmethod
  def make_queue_message(cls, _message_type, *args, **kwargs):
    if (WorkerClass := cls.get_worker_class_for_message(_message_type)) is None:
      raise Exception(
        f"Could not find a worker for {_message_type}"
        f" Please make sure a worker has this MESSAGE_TYPE and has been added to {__file__}:WORKER_CLASSES."
      )
    return QueueMessage(_message_type, WorkerClass.MessageBody.from_args(*args, **kwargs))

  def get_queue_name_from_message_group(self, message_group):
    assert isinstance(message_group, MessageGroup)
    queue_name = self.services.config_broker.get(f"queue.message_groups.{message_group.value}.pull_queue_name")
    return queue_name

  def get_queue_name_from_message_type(self, message_type):
    message_group = self.get_worker_class_for_message(message_type).MESSAGE_GROUP
    return self.get_queue_name_from_message_group(message_group)
