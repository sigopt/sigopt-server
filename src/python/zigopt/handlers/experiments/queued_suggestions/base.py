# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.net.errors import NotFoundError


class QueuedSuggestionHandler(ExperimentHandler):
  def __init__(self, services, request, experiment_id, queued_suggestion_id):
    if queued_suggestion_id is None:
      raise Exception("QueuedSuggestion id required")
    self.queued_suggestion_id = queued_suggestion_id
    self.queued_suggestion = None
    super().__init__(services, request, experiment_id)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "queued_suggestion": self._find_queued_suggestion(self.queued_suggestion_id),
      },
    )

  def can_act_on_objects(self, requested_permission, objects):
    experiment = objects["experiment"]
    queued_suggestion = objects["queued_suggestion"]
    return (
      super().can_act_on_objects(requested_permission, objects) and queued_suggestion.experiment_id == experiment.id
    )

  def _find_queued_suggestion(self, queued_suggestion_id):
    if (queued_suggestion := self.services.queued_suggestion_service.find_by_id(self.experiment_id, queued_suggestion_id)) is not None:
      if queued_suggestion.experiment_id == self.experiment_id:
        return queued_suggestion
    raise NotFoundError(f"No QueuedSuggestion {queued_suggestion_id} for experiment {self.experiment_id}")
