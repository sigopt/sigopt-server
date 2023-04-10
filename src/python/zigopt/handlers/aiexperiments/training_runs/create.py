# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds
from zigopt.handlers.aiexperiments.base import AiExperimentHandler
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.observations.create import CreatesObservationsMixin
from zigopt.handlers.experiments.suggestions.create import SuggestionsCreateHandler
from zigopt.handlers.training_runs.create import BaseTrainingRunsCreateHandler
from zigopt.handlers.validate.training_run import validate_assignments_meta
from zigopt.json.assignments import assignments_json
from zigopt.json.builder import TrainingRunJsonBuilder
from zigopt.net.errors import BadParamError, ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import OPTIMIZED_ASSIGNMENT_SOURCE, TrainingRun, is_completed_state
from zigopt.training_run.util import get_observation_values_dict_from_training_run_values_map


class AiExperimentTrainingRunsCreateHandler(
  AiExperimentHandler,
  CreatesObservationsMixin,
  BaseTrainingRunsCreateHandler,
  ExperimentHandler,
):
  authenticator = api_token_authentication
  required_permissions = WRITE

  make_suggestion_meta_from_json = SuggestionsCreateHandler.make_suggestion_meta_from_json

  def maybe_create_observation_from_data(self, assignments, values, failed):
    now = datetime_to_seconds(current_datetime())
    try:
      observation = self.create_observation(
        {
          "assignments": assignments,
          "values": values,
          "failed": failed,
        },
        timestamp=now,
      )
    except BadParamError:
      return None

    client = self.services.client_service.find_by_id(self.experiment.client_id)
    counts = self.services.observation_service.get_observation_counts(self.experiment.id)

    self.add_observations([observation], client, counts, optimize=True)

    return observation

  def get_assignments_relevant_to_experiment(self, training_run_params):
    provided_assignments = dict(training_run_params.training_run_data.assignments_struct)
    filtered_assignments = {}
    for name in self.experiment.all_parameters_map:
      try:
        value = provided_assignments[name]
        filtered_assignments[name] = value
      except KeyError:
        pass
    return filtered_assignments

  def get_observation_values(self, training_run_params):
    if training_run_params.training_run_data.state == TrainingRunData.FAILED:
      return None, True
    values = get_observation_values_dict_from_training_run_values_map(
      self.experiment, training_run_params.training_run_data.values_map
    )
    if len(values) == len(self.experiment.all_metrics):
      return values, False
    return None, True

  def maybe_create_observation_from_params(self, training_run_params):
    assignments = self.get_assignments_relevant_to_experiment(training_run_params)
    values, failed = self.get_observation_values(training_run_params)
    observation = self.maybe_create_observation_from_data(assignments, values, failed)
    if observation:
      observation_assignments = observation.get_assignments(self.experiment)
      return observation, assignments_json(self.experiment, observation_assignments)
    return None, {}

  def serve_suggestion(self):
    processed_suggestion_meta = SuggestionsCreateHandler.make_processed_suggestion_meta_from_json({})
    return self.services.suggestion_broker.serve_suggestion(
      experiment=self.experiment,
      processed_suggestion_meta=processed_suggestion_meta,
      auth=self.auth,
      automatic=True,
    )

  def maybe_create_explicit_suggestion_from_assignments(self, assignments):
    data = {"assignments": assignments}
    processed_suggestion_meta = SuggestionsCreateHandler.make_processed_suggestion_meta_from_json(data)
    try:
      return self.services.suggestion_broker.explicit_suggestion(
        experiment=self.experiment,
        suggestion_meta=self.make_suggestion_meta_from_json(data),
        processed_suggestion_meta=processed_suggestion_meta,
        automatic=True,
      )
    except BadParamError:
      return None

  def maybe_create_suggestion(self, training_run_params):
    provided_experiment_assignments = self.get_assignments_relevant_to_experiment(training_run_params)
    if provided_experiment_assignments:
      suggestion = self.maybe_create_explicit_suggestion_from_assignments(provided_experiment_assignments)
    else:
      suggestion = self.serve_suggestion()
    assignments_update = {}
    if suggestion:
      assignments_update = assignments_json(self.experiment, suggestion.get_assignments(self.experiment))
    return suggestion.processed if suggestion else None, assignments_update

  def maybe_create_suggestion_and_observation(self, training_run_params):
    if is_completed_state(training_run_params.training_run_data.state):
      observation, assignments_update = self.maybe_create_observation_from_params(training_run_params)
      return None, observation, assignments_update
    suggestion, assignments_update = self.maybe_create_suggestion(training_run_params)
    return suggestion, None, assignments_update

  def handle(self, params):
    if self.experiment.deleted:
      raise BadParamError(f"Cannot create training runs for deleted experiment {self.experiment.id}")

    project = self.services.project_service.find_by_client_and_id(
      self.experiment.client_id,
      self.experiment.project_id,
    )

    if not self.experiment.runs_only:
      raise ForbiddenError(f"Experiment {self.experiment.id} cannot create training runs")
    if project is None:
      raise ForbiddenError(f"Experiment {self.experiment.id} must belong to a project in order to create training runs")
    suggestion, observation, assignments = self.maybe_create_suggestion_and_observation(params.training_run_params)
    params.training_run_params.training_run_data.assignments_struct.update(assignments)

    training_run_data = params.training_run_params.training_run_data
    assignments_meta = training_run_data.assignments_meta
    if assignments_meta is not None:
      validate_assignments_meta(training_run_data.assignments_struct, assignments_meta, None)
    if suggestion:
      for assignment in assignments.keys():
        params.training_run_params.training_run_data.assignments_meta[assignment].source = OPTIMIZED_ASSIGNMENT_SOURCE
      params.training_run_params.training_run_data.assignments_sources[OPTIMIZED_ASSIGNMENT_SOURCE].sort = 1
      params.training_run_params.training_run_data.assignments_sources[OPTIMIZED_ASSIGNMENT_SOURCE].default_show = True

    training_run_data = params.training_run_params.training_run_data
    reported_state = training_run_data.state
    training_run_data.state = reported_state

    new_training_run = TrainingRun(
      client_id=self.experiment.client_id,
      created_by=(self.auth.current_user and self.auth.current_user.id),
      experiment_id=self.experiment.id,
      project_id=self.experiment.project_id,
      suggestion_id=suggestion and suggestion.suggestion_id,
      observation_id=observation and observation.id,
      training_run_data=training_run_data,
    )
    self.services.training_run_service.insert_training_runs([new_training_run])

    self.services.experiment_service.mark_as_updated(self.experiment)
    checkpoint_count = 0

    return TrainingRunJsonBuilder(
      training_run=new_training_run,
      checkpoint_count=checkpoint_count,
      project=project,
    )
