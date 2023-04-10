# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import AiExperimentJsonBuilder
from zigopt.net.errors import NotFoundError


class AiExperimentHandler(ExperimentHandler):
  allow_development = False
  JsonBuilder = AiExperimentJsonBuilder
  redirect_ai_experiments = False

  def find_objects(self):
    objs = super().find_objects()
    experiment = objs["experiment"]
    if not experiment.runs_only:
      raise NotFoundError(f"The AiExperiment {self.experiment_id} does not exist")
    return objs

  def can_act_on_objects(self, requested_permission, objects):  # pylint: disable=useless-parent-delegation
    return super().can_act_on_objects(requested_permission, objects)
