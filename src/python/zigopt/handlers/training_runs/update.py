# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy.sql.functions import coalesce as sql_coalesce

from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds
from zigopt.common.struct import ImmutableStruct
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.observations.create import CreatesObservationsMixin
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.handlers.training_runs.parser import TrainingRunRequestParams, TrainingRunRequestParser
from zigopt.handlers.validate.training_run import validate_assignments_meta
from zigopt.json.builder.training_run import TrainingRunJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import TrainingRun, is_completed_state

from libsigopt.aux.errors import InvalidValueError, SigoptValidationError


class TrainingRunsUpdateHandler(CreatesObservationsMixin, TrainingRunHandler):
  """Update a training run.
    This endpoint allows updating a training run. Note that there are two HTTP verbs that can be used with this
    endpoint, PUT and MERGE. The difference is behavior for lists and maps: PUT will replace all values, MERGE will
    recursively merge. This means that MERGE can save bandwidth but is tricky to delete, so the caller will
    have to pay attention to which verb they use. This also simplifies client behavior: to add something to a map they
    don't need to keep track of the full state, just add the new objects. This also simplies behaviors with
    multiple clients: no need for check-and-set mechanics or any of the other ways to resolve multiple requests, as
    long as the desired behavior is purely append-only to maps and changing direct fields, MERGE will save bandwidth
    and simplify the caller and the servers. To delete from a map, with PUT you can simply drop the field and not
    include it, but with MERGE you will have to explicitly set that field to null.
    ---
    tags:
      - "training runs"
    requestBody:
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/TrainingRunPut"
    parameters:
      - $ref: "#/components/parameters/TrainingRunId"
    responses:
      200:
        description: "Training Run updated."
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TrainingRun'
      204:
        description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                      returned instead of 200, without any data."
      401:
        description: "Unauthorized. Authorization was incorrect."
      400:
        description: "Bad Request Format. Failed validation of some kind."
      404:
        description: "Not found. No experiment is at that URI."
      429:
        description: "Client has engaged too many events recently and is rate limited."
      5XX:
        description: "Unexpected Error"
    components:
      responses:
        429:
          description: "Client has engaged too many events recently and is rate limited."
      parameters:
        TrainingRunId:
          in: path
          name: training_run_id
          required: true
          schema:
            type: integer
            minimum: 1
          description: "The id of the training_run that the caller is interested in."
      schemas:
        TrainingRunPut:
          allOf:
              - $ref: "#/components/schemas/TrainingRunBase"
              - type: object
                required: [name, state, project]
                properties:
                  project:
                    type: string
                    minLength: 1
                    maxLength: 32
                    description: "The id of the project that this training_run is associated with."
    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct("Params", ["skip_response_content", "merge_objects", "training_run_params"])

  experiment: Experiment | None
  training_run: TrainingRun | None

  def parse_params(self, request):
    unaccepted_params = request.params().keys() - TrainingRunRequestParams.valid_fields
    if unaccepted_params:
      raise SigoptValidationError(f"Unknown parameters: {unaccepted_params}")

    method = request.method.lower()
    assert method in ("put", "merge")
    merge_objects = method == "merge"
    return self.Params(
      skip_response_content=request.skip_response_content,
      merge_objects=merge_objects,
      training_run_params=TrainingRunRequestParser().parse_params(request),
    )

  def _ensure_field_cannot_be_removed(self, params, user_name):
    if params.training_run_params.field_is_explicitly_null(user_name):
      raise SigoptValidationError(f"Cannot remove {user_name} from a run")

  def _create_observation_from_suggestion(self, training_run: TrainingRun, updated_timestamp):
    assert self.experiment is not None

    client = self.services.client_service.find_by_id(training_run.client_id)
    counts = self.services.observation_service.get_observation_counts(self.experiment.id)
    if training_run.state == TrainingRunData.FAILED:
      values, failed = [], True
    else:
      values = training_run.get_observation_values(self.experiment)
      if len(values) == len(self.experiment.all_metrics):
        failed = False
      else:
        values, failed = [], True
    observation = self.create_observation(
      {
        "suggestion": training_run.suggestion_id,
        "values": values,
        "failed": failed,
      },
      datetime_to_seconds(updated_timestamp),
    )
    self.add_observations([observation], client, counts, optimize=True)
    self.emit_update({TrainingRun.observation_id: observation.id})

  def _ensure_observation_exists(self, training_run, updated_timestamp):
    if self.experiment is None:
      return
    if training_run.observation_id is not None:
      return
    if training_run.suggestion_id is not None:
      suggestion = self.services.suggestion_service.find_by_id(training_run.suggestion_id)
      if suggestion is None or not suggestion.automatic:
        return
      self._create_observation_from_suggestion(training_run, updated_timestamp)

  def handle(self, params):
    assert self.auth is not None
    assert self.training_run is not None
    assert self.project is not None

    self._ensure_field_cannot_be_removed(params, "state")
    self._ensure_field_cannot_be_removed(params, "name")
    self._ensure_field_cannot_be_removed(params, "project")

    if self.training_run.experiment_id is not None:
      self.experiment = self.services.experiment_service.find_by_id(
        self.training_run.experiment_id, include_deleted=True
      )

    update_clause = {}
    now = current_datetime()

    training_run_data = params.training_run_params.training_run_data
    assignments_meta = training_run_data.assignments_meta
    if assignments_meta is not None:
      validate_assignments_meta(training_run_data.assignments_struct, assignments_meta, self.training_run)

    if params.training_run_params.deleted is not None:
      update_clause[TrainingRun.deleted] = params.training_run_params.deleted

    new_project = None
    if params.training_run_params.project:
      new_project = self.services.project_service.find_by_client_and_reference_id(
        self.training_run.client_id,
        params.training_run_params.project,
      )
      if new_project and self.auth.can_act_on_project(self.services, WRITE, new_project):
        update_clause[TrainingRun.project_id] = new_project.id
      else:
        raise InvalidValueError(f"Unknown project ID: {params.training_run_params.project}")

    if params.training_run_params.training_run_data_json:
      update_clause[TrainingRun.training_run_data] = self.create_update_clause(
        params.merge_objects,
        params.training_run_params.training_run_data_json,
      )

    if is_completed_state(params.training_run_params.training_run_data.state):
      update_clause[TrainingRun.completed] = sql_coalesce(TrainingRun.completed, now)

    previous_deleted = self.training_run.deleted
    new_deleted = update_clause.pop(TrainingRun.deleted, previous_deleted)

    if new_deleted != previous_deleted:
      self.services.training_run_service.set_deleted(self.training_run.id, deleted=new_deleted)

    if update_clause:
      update_clause[TrainingRun.updated] = now
      self.emit_update(update_clause)

    training_run = self.services.training_run_service.find_by_id(self.training_run.id)
    assert training_run

    if is_completed_state(training_run.training_run_data.state):
      self._ensure_observation_exists(training_run, now)
      training_run = self.services.training_run_service.find_by_id(self.training_run.id)
      assert training_run

    if params.skip_response_content:
      return None

    checkpoint_count = self.services.checkpoint_service.count_by_training_run(self.training_run.id)
    return TrainingRunJsonBuilder(
      training_run=training_run,
      checkpoint_count=checkpoint_count,
      project=new_project or self.project,
    )
