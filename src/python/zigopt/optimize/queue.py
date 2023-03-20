# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.queue.message_types import MessageType
from zigopt.services.base import Service


class OptimizeQueueService(Service):
  def enqueue_optimization(
    self,
    experiment,
    num_observations,
    force=False,
    should_enqueue_hyper_opt=True,
  ):
    if self.services.config_broker.get("queue.enabled", True) and self.services.config_broker.get(
      "queue.message_groups.optimization.enabled", True
    ):
      messages = remove_nones(
        [
          *self._maybe_enqueue_next_points(experiment, force=force),
          *self._maybe_enqueue_optimize(
            experiment,
            should_enqueue_hyper_opt,
            force=force,
          ),
          *self._maybe_enqueue_importances(experiment, num_observations, force=force),
        ]
      )
      self.services.queue_monitor.robust_enqueue(messages, experiment)

  @generator_to_list
  def _maybe_enqueue_next_points(self, experiment, force):
    yield self.services.message_router.make_queue_message(
      MessageType.NEXT_POINTS,
      experiment_id=experiment.id,
      force=force,
    )

  @generator_to_list
  def _maybe_enqueue_optimize(self, experiment, should_enqueue_hyper_opt, force):
    if should_enqueue_hyper_opt:
      yield self.services.message_router.make_queue_message(
        MessageType.OPTIMIZE,
        experiment_id=experiment.id,
        force=force,
      )

  def _create_importances_message(self, experiment, num_observations, force):
    if self.services.config_broker.get(
      "features.importances", True
    ) and self.services.importances_service.can_update_importances(experiment, num_observations):
      return self.services.message_router.make_queue_message(
        MessageType.IMPORTANCES,
        experiment_id=experiment.id,
        force=force,
      )
    return None

  @generator_to_list
  def _maybe_enqueue_importances(self, experiment, num_observations, force):
    message = self._create_importances_message(experiment, num_observations, force)
    if message is not None:
      if self.services.importances_service.should_update_importances(experiment, num_observations) or force:
        yield message

  def always_enqueue_importances(self, experiment, num_observations):
    return self._create_importances_message(experiment, num_observations, force=True)
