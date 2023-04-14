# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from datetime import timedelta

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp_with_microseconds
from zigopt.redis.service import RedisServiceError
from zigopt.services.base import Service


DEFAULT_MAX_ALERT_TIME = timedelta(minutes=15).total_seconds()
DEFAULT_MAX_ENQUEUE_DELTA = timedelta(minutes=10).total_seconds()
DEFAULT_MAX_FLIGHT_TIME = timedelta(minutes=10).total_seconds()

LAST_ALERT = "last_alert"
LAST_DEQUEUE = "last_dequeue"
LAST_ENQUEUE = "last_enqueue"
LAST_EMPTY = "last_empty"


class QueueMonitor(Service):
  def robust_enqueue(self, queue_messages, experiment):
    """
        Enqueue an obeservation. If the queue is down, log an error and proceed in production.

        :param queue_messages: The observation/hyperparameter message to enqueue
        :type queue_messages: Sequence of zigopt.queue.message.QueueMessage
        :param experiment: The experiment that the observation is from
        :type experiment: zigopt.experiment.model.Experiment

        """
    now = unix_timestamp_with_microseconds()
    enqueue_time = int(now)
    queue_messages_by_group_key = as_grouped_dict(
      queue_messages,
      self.services.queue_message_grouper.group_key_for_queue_message,
    )
    for group_key, queue_message_batch in queue_messages_by_group_key.items():
      with self.services.exception_logger.tolerate_exceptions(
        Exception, {"experiment_id": experiment and experiment.id}
      ):
        queue_names = distinct(
          [self.services.queue_service.get_queue_name_from_message_type(m.message_type) for m in queue_message_batch]
        )
        for queue_name in queue_names:
          self.before_enqueue(queue_name, now)
        message_score = enqueue_time
        self.services.queue_service.enqueue_batch(
          queue_messages=queue_message_batch,
          group_key=group_key,
          enqueue_time=enqueue_time,
          message_score=message_score,
        )

  def before_enqueue(self, queue_name, now):
    if self.should_monitor(queue_name):
      new_status = {
        LAST_ENQUEUE: now,
      }

      # Whenever the queue is empty, we can "reset" our progress, as all messages have
      # been processed. So, whenever we reach an empty queue we do not need to be
      # concerned about any events prior to that.
      #
      # The reason we make this check is so that the first enqueue is an empty queue
      # does not trigger an alert (because last_dequeue could have been a long time
      # ago).
      is_empty = self.is_queue_empty(queue_name)
      if is_empty:
        new_status[LAST_EMPTY] = now

      self._update_status(queue_name, new_status)

      if not is_empty:
        self.check_for_queue_backup(queue_name, now)

  def after_dequeue(self, queue_name, message):
    if self.should_monitor(queue_name):
      now = unix_timestamp_with_microseconds()
      self._update_status(
        queue_name=queue_name,
        status={LAST_DEQUEUE: now},
      )
      self.inspect_message(queue_name, message, now)

  def _queue_monitor_name(self, queue_name):
    return self.services.redis_key_service.create_queue_name_key("queue-monitor", queue_name, ":")

  def _get_status(self, queue_name):
    return remove_nones(
      {
        key.decode(): napply(value, float)
        for key, value in self.services.redis_service.get_all_hash_fields(self._queue_monitor_name(queue_name)).items()
      }
    )

  def _update_status(self, queue_name, status):
    with self.services.exception_logger.tolerate_exceptions(RedisServiceError):
      status = remove_nones(status)
      if status:
        self.services.redis_service.set_hash_fields(self._queue_monitor_name(queue_name), status)

  def _can_send_alert(self, status, now):
    last_alert = status.get(LAST_ALERT) or 0
    seconds_since_alert = now - last_alert
    return seconds_since_alert > self.services.config_broker.get("qworker.maxAlertFrequency", DEFAULT_MAX_ALERT_TIME)

  def should_monitor(self, queue_name):
    return self.services.config_broker.get("queue.monitor", True)

  def check_for_queue_backup(self, queue_name, now):
    with self.services.exception_logger.tolerate_exceptions(RedisServiceError):
      queue_status = self._get_status(queue_name)
      last_progress = max_option(
        remove_nones_sequence(
          (
            queue_status.get(LAST_DEQUEUE),
            queue_status.get(LAST_EMPTY),
          ),
          list,
        )
      )
      last_enqueue = queue_status.get(LAST_ENQUEUE)
      delta_in_seconds = None
      if last_enqueue is not None and last_progress is not None:
        delta_in_seconds = last_enqueue - last_progress

      if (
        self._can_send_alert(queue_status, now)
        and delta_in_seconds is not None
        and delta_in_seconds > self.services.config_broker.get("qworker.maxEnqueueDelta", DEFAULT_MAX_ENQUEUE_DELTA)
      ):
        self.services.exception_logger.log_exception(
          "The queues might be backed up - no messages have been processed for a long time.",
        )
        self._update_status(queue_name, {LAST_ALERT: now})

  def inspect_message(self, queue_name, message, now):
    enqueue_time = message.enqueue_time
    with self.services.exception_logger.tolerate_exceptions(RedisServiceError):
      queue_status = self._get_status(queue_name)
      if (
        self._can_send_alert(queue_status, now)
        and enqueue_time
        and (now - enqueue_time) > self.services.config_broker.get("qworker.maxFlightTime", DEFAULT_MAX_FLIGHT_TIME)
      ):
        self.services.exception_logger.log_exception(
          "The queues might be backed up - a very old message was processed.",
        )
        self._update_status(queue_name, {LAST_ALERT: now})

  def is_queue_empty(self, queue_name):
    messages_queued = self.services.queue_service.count_queued_messages(queue_name)
    if messages_queued <= 0:
      return True
    return False
