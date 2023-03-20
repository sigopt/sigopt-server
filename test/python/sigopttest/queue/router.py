# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import pytest

from zigopt.common import *
from zigopt.optimize.worker import NextPointsWorker
from zigopt.queue.message_types import MessageType
from zigopt.queue.router import WORKER_CLASSES, MessageRouter


@pytest.fixture
def services():
  return mock.Mock()


@pytest.fixture
def router(services):
  return MessageRouter(services)


@pytest.mark.parametrize("WorkerClass", WORKER_CLASSES)
def test_get_worker_class_for_message(router, WorkerClass):
  assert issubclass(router.get_worker_class_for_message(WorkerClass.MESSAGE_TYPE), WorkerClass)


def make_message(WorkerClass, router):
  return router.make_queue_message(WorkerClass.MESSAGE_TYPE)


@pytest.mark.parametrize("WorkerClass", WORKER_CLASSES)
def test_worker(router, WorkerClass):
  message = make_message(WorkerClass, router)
  deserialized_message = router.deserialize_message(message.message_type, message.serialized_body)
  assert deserialized_message is not None
  assert deserialized_message.deserialized_message == message.deserialized_message


def test_next_points_worker(router):
  assert router.get_worker_class_for_message(MessageType.NEXT_POINTS) == NextPointsWorker
  message = router.make_queue_message(
    MessageType.NEXT_POINTS,
    experiment_id=3,
    force=True,
  )
  deserialized_message = router.deserialize_message(message.message_type, message.serialized_body)
  assert deserialized_message is not None
  assert deserialized_message.deserialized_message == message.deserialized_message


def test_unknown_worker(router):
  assert router.get_worker_class_for_message("fake_message_type") is None
  assert router.deserialize_message("fake_message_type", "fake_message_body") is None
