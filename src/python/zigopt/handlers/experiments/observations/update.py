# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.observations.base import ObservationHandler
from zigopt.handlers.experiments.observations.create import CreatesObservationsMixin
from zigopt.handlers.validate.observation import validate_observation_json_dict_for_update
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.json.builder import ObservationJsonBuilder
from zigopt.observation.data import update_observation_data
from zigopt.observation.from_json import update_observation_data_assignments_task_from_json
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.lib import copy_protobuf


class ObservationsUpdateHandler(CreatesObservationsMixin, ObservationHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  experiment: Experiment | None
  observation: Observation | None

  def parse_params(self, request):
    return request.params()

  def handle(self, json_dict):  # type: ignore
    assert self.experiment is not None
    assert self.observation is not None

    validate_observation_json_dict_for_update(json_dict, self.experiment, self.observation)
    no_optimize = get_opt_with_validation(json_dict, "no_optimize", ValidationType.boolean)

    now = current_datetime()
    new_observation_data = copy_protobuf(self.observation.data)
    new_observation_data.timestamp = int(datetime_to_seconds(now))
    num_observations = self.services.observation_service.count_by_experiment(self.experiment)

    self.observation_from_json(
      json_dict=json_dict,
      observation=self.observation,
      observation_data=new_observation_data,
      observation_data_create_update_handler=update_observation_data,
      assignments_handler=update_observation_data_assignments_task_from_json,
      timestamp=None,
    )

    self.services.database_service.update_one(
      self.services.database_service.query(Observation).filter_by(id=self.observation.id),
      {
        Observation.processed_suggestion_id: self.observation.processed_suggestion_id,
        Observation.data: new_observation_data,
      },
    )
    self.services.experiment_service.mark_as_updated(self.experiment, now)

    self.observation.data = new_observation_data

    if no_optimize is not True:
      self.services.observation_service.optimize(
        experiment=self.experiment,
        num_observations=num_observations,
      )

    return ObservationJsonBuilder(self.experiment, self.observation)
