# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.net.errors import NotFoundError


class ObservationHandler(ExperimentHandler):
  def __init__(self, services, request, experiment_id, observation_id):
    if observation_id is None:
      raise Exception("Observation id required")
    self.observation_id = observation_id
    self.observation = None
    super().__init__(services, request, experiment_id)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "observation": self._find_observation(self.observation_id),
      },
    )

  def _find_observation(self, observation_id):
    observation = self.services.observation_service.find_by_id(observation_id)
    if observation is not None:
      if observation.experiment_id == self.experiment_id:
        return observation
    raise NotFoundError(f"No observation {observation_id} for experiment {self.experiment_id}")

  def can_act_on_objects(self, requested_permission, objects):
    observation = objects["observation"]
    experiment = objects["experiment"]
    return super().can_act_on_objects(requested_permission, objects) and observation.experiment_id == experiment.id
