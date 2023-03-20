# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import time

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.util import DeleteClause
from zigopt.protobuf.gen.queue.messages_pb2 import NextPointsMessage, OptimizeHyperparametersMessage
from zigopt.queue.message import ProtobufMessageBody
from zigopt.queue.message_groups import MessageGroup
from zigopt.queue.message_types import MessageType
from zigopt.queue.worker import QueueWorker


class ExperimentWorker(QueueWorker):
  MESSAGE_GROUP = MessageGroup.OPTIMIZATION

  def get_experiment(self, experiment_id):
    experiment = self.services.experiment_service.find_by_id(experiment_id, include_deleted=True)
    return experiment

  def should_handle(self, e):
    return e and not e.deleted and e.id

  def _handle_message(self, message):
    experiment_id = message.experiment_id
    if not experiment_id:
      raise Exception("No experiment id")

    experiment = self.get_experiment(experiment_id)
    logger = self.get_logger()
    latest_observation_id = self.services.observation_service.latest_observation_id(experiment.id)
    logging_info = dict(
      client=str(experiment.client_id),
      experiment=str(experiment.id),
      latest_observation_id=str(latest_observation_id),
    )
    timing_info = {}
    if self.should_handle(experiment):
      logger.info("Processing message for experiment %s", experiment.id)
      start_time = time.time()
      if self.enqueue_time is not None:
        # NOTE: time_avail is not accurate since we remove the millis (time.time() has sub-second precision)
        timing_info["time_avail"] = start_time - self.enqueue_time
      logger.info(
        json.dumps(
          remove_nones(
            dict(
              state="processing",
              **logging_info,
              **timing_info,
            )
          )
        )
      )
      self.process(experiment, message)
      finish_time = time.time()
      timing_info["time_proc"] = finish_time - start_time
      # NOTE: include deleted because this is a proxy for user actions and it makes the query much faster
      observation_count = self.services.observation_service.count_by_experiment(
        experiment,
        deleted=DeleteClause.ALL,
      )
      timing_info["obs_count"] = observation_count
      approx_time_between_observations = None
      if observation_count:
        approx_time_between_observations = (current_datetime() - experiment.date_created) / observation_count
        approx_time_between_observations = approx_time_between_observations.total_seconds()
        timing_info["time_obs"] = approx_time_between_observations
      if self.enqueue_time is not None and start_time > self.enqueue_time:
        timing_info["time_tot"] = finish_time - self.enqueue_time
        # NOTE: the approximate fraction of time available and proccessing of the messages total lifecycle
        timing_info["frac_avail"] = timing_info["time_avail"] / timing_info["time_tot"]
        timing_info["frac_proc"] = timing_info["time_proc"] / timing_info["time_tot"]
        if timing_info.get("time_obs"):
          # NOTE: the approximate fraction of time total, available and proccessing per observation
          timing_info["est_obs_tot"] = timing_info["time_tot"] / timing_info["time_obs"]
          timing_info["est_obs_avail"] = timing_info["time_avail"] / timing_info["time_obs"]
          timing_info["est_obs_proc"] = timing_info["time_proc"] / timing_info["time_obs"]
      logger.info("Finished processing for experiment %s", experiment.id)
      logger.info(
        json.dumps(
          remove_nones(
            dict(
              state="finished",
              **logging_info,
              **timing_info,
            )
          )
        )
      )
    else:
      skip_time = time.time()
      if self.enqueue_time is not None and skip_time > self.enqueue_time:
        timing_info["time_tot"] = skip_time - self.enqueue_time
      logger.warning("Skipping unneeded processing for experiment %s", experiment_id)
      logger.warning(
        json.dumps(
          remove_nones(
            dict(
              state="skipped",
              **logging_info,
              **timing_info,
            )
          )
        )
      )

  def get_logger(self):
    return self.services.logging_service.getLogger(f"sigopt.optimize.{self.MESSAGE_TYPE}")

  def process(self, experiment, message):
    raise NotImplementedError()


class NextPointsWorker(ExperimentWorker):
  MESSAGE_TYPE = MessageType.NEXT_POINTS

  class MessageBody(ProtobufMessageBody):
    PROTOBUF_CLASS = NextPointsMessage

  def process(self, experiment, message):
    return self.services.optimizer.trigger_next_points(experiment)


class HyperparameterOptimizationWorker(ExperimentWorker):
  MESSAGE_TYPE = MessageType.OPTIMIZE

  class MessageBody(ProtobufMessageBody):
    PROTOBUF_CLASS = OptimizeHyperparametersMessage

  def process(self, experiment, message):
    return self.services.optimizer.trigger_hyperparameter_optimization(experiment)
