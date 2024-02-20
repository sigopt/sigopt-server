# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64
import signal
import time

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.exception.logger import AlreadyLoggedException
from zigopt.profile.tracer import NullTracer
from zigopt.queue.exceptions import (
  WorkerException,
  WorkerFinishedException,
  WorkerInterruptedException,
  WorkerKilledException,
)
from zigopt.queue.message_groups import MessageGroup

from libsigopt.aux.errors import SigoptComputeError


# A way for the queue workers to detect that it should stop processing messages and shut down.
# Uses signals so that `sudo service workerd-multi stop` works as expected
class SignalKillPolicy:
  def __init__(self):
    self._should_kill = False
    signal.signal(signal.SIGINT, self._shutdown)
    signal.signal(signal.SIGTERM, self._shutdown)

  def _shutdown(self, signum, frame):
    del signum
    del frame
    self._should_kill = True

  def should_kill(self):
    return self._should_kill


class NullKillPolicy:
  def should_kill(self):
    return False


class QueueMessageHandler:
  def __init__(self, global_services):
    self.global_services = global_services

  @property
  def logger(self):
    return self.global_services.logging_service.getLogger("sigopt.queue.workers.messages")

  def monitor_message(self, services, queue_name, message):
    services.queue_monitor.after_dequeue(queue_name, message)
    return services.message_tracking_service.process_one_message(queue_name)

  def submit(self, WorkerClass, services, message):
    WorkerClass(services, message).handle()


class QueueWorkers(QueueMessageHandler):
  def __init__(self, message_group, global_services, request_local_services_factory, profiler, kill_policy=None):
    assert isinstance(message_group, MessageGroup)
    super().__init__(global_services)
    self.request_local_services_factory = request_local_services_factory
    self.kill_policy = kill_policy or NullKillPolicy()
    self.profiler = profiler
    self.tracer = None
    self.jitter = 0
    self.message_count = 0
    self.message_group = message_group
    self._get_pull_queue_name()

  def _get_pull_queue_name(self):
    if (
      queue_name := self.global_services.message_router.get_queue_name_from_message_group(self.message_group)
    ) is None:
      raise Exception(f"Missing queue name for {self.message_group}")
    return queue_name

  @property
  def pull_queue_name(self):
    return self._get_pull_queue_name()

  @property
  def logger(self):
    return self.global_services.logging_service.getLogger("sigopt.queue.workers")

  def test(self):
    self.global_services.queue_service.test(self.pull_queue_name)

  def _check_stop_conditions(self, base_max_messages):
    if self.kill_policy.should_kill():
      self.logger.info("QueueWorkers killed by kill policy")
      raise WorkerKilledException()

    if (
      max_messages_threshold := coalesce(
        base_max_messages,
        self.global_services.config_broker.get(f"queue.{self.message_group.value}.max_messages"),
      )
    ) is None:
      should_process = True
    else:
      max_messages_threshold = max(max_messages_threshold, self.jitter * 2)
      should_process = self.message_count < max_messages_threshold + self.jitter

    if should_process:
      return
    raise WorkerFinishedException()

  def _consume_and_process_one_message(self, queue_name, process_message, wait_time_seconds):
    consume_time = current_datetime()
    consumed = False
    self.global_services.exception_logger.reset_extra()
    self.global_services.exception_logger.add_extra(
      consume_time=str(consume_time),
      queue_name=queue_name,
    )
    self.global_services.exception_logger.set_tracer(self.tracer)
    try:
      consumed = self._consume_message_from_queue(queue_name, process_message, wait_time_seconds)
    except Exception as e:
      fail_time = current_datetime()
      duration = fail_time - consume_time
      self.global_services.exception_logger.log_exception(
        e,
        extra={
          "time_failed_utc": str(fail_time),
          "duration": str(duration),
        },
      )
      # Treat unhandled exceptions as fatal, so the process dies and gets respawned.
      # We want to clean up after unhandled errors (such as MemoryErrors) so that we
      # are not proceeding in an unrecoverable state
      self.logger.error("QueueWorkers shutting down due to fatal error")
      raise
    if not consumed:
      time.sleep(non_crypto_random.uniform(1, 2))

    return consumed

  def _consumption_loop(
    self,
    *,
    queue_name,
    process_message,
    max_messages,
    message_count_increment,
    wait_time_seconds,
    exit_if_no_messages,
  ):
    while True:
      self._check_stop_conditions(base_max_messages=max_messages)
      self.message_count += message_count_increment
      consumed = self._consume_and_process_one_message(
        queue_name or self.pull_queue_name,
        process_message,
        wait_time_seconds,
      )
      if exit_if_no_messages and not consumed:
        break

  def run(self, max_messages=None, max_messages_jitter=None):
    self.tracer = NullTracer()

    jitter_bounds = coalesce(
      max_messages_jitter,
      self.global_services.config_broker.get(f"queue.{self.message_group.value}.max_messages_jitter", 0),
    )
    self.jitter = non_crypto_random.randint(-jitter_bounds, jitter_bounds)  # pylint: disable=invalid-unary-operand-type

    self.message_count = 0
    self.profiler.enable()

    worker_exc = None
    try:
      self._consumption_loop(
        max_messages=max_messages,
        queue_name=None,
        process_message=self._process_worker_message,
        wait_time_seconds=None,
        message_count_increment=1,
        exit_if_no_messages=False,
      )
    except WorkerException as exc:
      worker_exc = exc

    if worker_exc is None:
      self.global_services.exception_logger.soft_exception(
        "Unexpected graceful exit from QueueWorkers._consumption_loop"
      )

    self.profiler.disable()
    self.profiler.print_stats()

    self.logger.info("QueueWorkers shutting down safely")

    if isinstance(worker_exc, WorkerInterruptedException):
      raise worker_exc

  def _process_worker_message(self, worker, services, message):
    self.submit(worker, services, message)

  def _consume_message_from_queue(self, queue_name, process_message, wait_time_seconds):
    assert self.tracer is not None

    message = None
    with self.global_services.exception_logger.tolerate_exceptions(Exception):
      message = self.global_services.queue_service.dequeue(queue_name, wait_time_seconds=wait_time_seconds)
    if not message:
      return False

    message_type = message.message_type
    self.global_services.exception_logger.add_extra(message_type=message_type)

    with self.tracer.trace_background_task(message.message_type, "Message"):
      base64_encoded_body = base64.b64encode(message.serialized_body)

      self.tracer.set_attribute("queue_name", queue_name)
      self.tracer.set_attribute("body", base64_encoded_body)
      self.tracer.set_attribute("message_type", message.message_type)

      WorkerClass = self.global_services.message_router.get_worker_class_for_message(message.message_type)
      if not WorkerClass:
        # Indicates that this qworker does not know how to handle this message.
        # Previously, we would re-enqueue this, but that could lead to a runaway
        # message that is re-enqueued indefinitely. Instead, we will prefer to
        # fail fast here and let the deadletter queue capture any messages that
        # were not handled
        self.global_services.exception_logger.soft_exception(f"No worker to handle {message.message_type}")
        self.global_services.queue_service.reject(message, queue_name)
        return False

      self.logger.info("%s %s", message.message_type, message.deserialized_message)
      readable_message_content = message.deserialized_message and str(message.deserialized_message)
      self.tracer.set_attribute("message", readable_message_content)
      self.global_services.exception_logger.add_extra(
        queue_message={
          "body": base64_encoded_body,
          "message": readable_message_content,
          "message_type": message_type,
        },
      )

      services = self.request_local_services_factory(self.global_services)
      services.database_service.start_session()
      try:
        with self.monitor_message(services, queue_name, message):
          process_message(WorkerClass, services, message)
      except SigoptComputeError as e:
        self.global_services.queue_service.reject(message, queue_name)
        raise AlreadyLoggedException(e) from e
      except AssertionError:
        raise
      except Exception as e:
        self.global_services.exception_logger.log_exception(e)
        self.global_services.queue_service.reject(message, queue_name)
        raise AlreadyLoggedException(e) from e
      else:
        self.global_services.queue_service.delete(message, queue_name)
      finally:
        services.database_service.end_session()
    return True
