# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.net.errors import NotFoundError


class SuggestionHandler(ExperimentHandler):
  def __init__(self, services, request, experiment_id, suggestion_id):
    if suggestion_id is None:
      raise Exception("Suggestion id required")
    self.suggestion_id = suggestion_id
    self.suggestion = None
    super().__init__(services, request, experiment_id)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "suggestion": self._find_suggestion(self.suggestion_id),
      },
    )

  def _find_suggestion(self, suggestion_id):
    suggestion = self.services.suggestion_service.find_by_id(suggestion_id)
    if suggestion is not None:
      if suggestion.experiment_id == self.experiment_id:
        return suggestion
    raise NotFoundError(f"No suggestion {suggestion_id} for experiment {self.experiment_id}")

  def can_act_on_objects(self, requested_permission, objects):
    suggestion = objects["suggestion"]
    experiment = objects["experiment"]
    return super().can_act_on_objects(requested_permission, objects) and suggestion.experiment_id == experiment.id
