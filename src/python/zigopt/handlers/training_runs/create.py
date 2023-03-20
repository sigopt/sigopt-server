# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.training_runs.parser import TrainingRunRequestParams, TrainingRunRequestParser
from zigopt.handlers.validate.training_run import validate_assignments_meta
from zigopt.json.builder import PaginationJsonBuilder, TrainingRunJsonBuilder
from zigopt.net.errors import BadParamError, MissingParamError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import TrainingRun


MAX_RUNS_BATCH_CREATE_COUNT = 10000

# customlint: disable=AccidentalFormatStringRule


def get_default_max_batch_runs(services):
  return services.config_broker.get(
    "features.maxRunsBatchCreateCount",
    MAX_RUNS_BATCH_CREATE_COUNT,
  )


class BaseTrainingRunsCreateHandler(Handler):
  required_permissions = WRITE

  Params = ImmutableStruct("Params", ["training_run_params"])

  def parse_params(self, request):
    return self.parse_request(request)

  def parse_request(self, request):
    unaccepted_params = request.params().keys() - TrainingRunRequestParams.valid_fields
    if unaccepted_params:
      raise BadParamError(f"Unknown parameters: {unaccepted_params}")

    training_run_params = TrainingRunRequestParser().parse_params(request)
    if not training_run_params.training_run_data.name:
      raise MissingParamError("name")
    if training_run_params.field_is_explicitly_null("state"):
      raise BadParamError("state cannot be `null`")
    if training_run_params.project is not None or training_run_params.field_is_explicitly_null("project"):
      raise BadParamError("`project` is not a valid JSON key for this endpoint.")

    assignments_meta = training_run_params.training_run_data.assignments_meta
    if assignments_meta is not None:
      validate_assignments_meta(training_run_params.training_run_data.assignments_struct, assignments_meta, None)

    return self.Params(training_run_params=training_run_params)

  def get_validated_reported_state(self, training_run_data):
    if not training_run_data.HasField("state"):
      return TrainingRunData.ACTIVE

    return training_run_data.state


class ProjectsTrainingRunsCreateHandler(ProjectHandler, BaseTrainingRunsCreateHandler):
  """Create a new trainign run for a specific client project.
    This creates a new training run- a combination of suggestion, results, and other information, in the specified
    client and project.
    ---
    tags:
      - "training runs"
    requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/TrainingRunPost"
    parameters:
      - $ref: "#/components/parameters/ClientId"
      - $ref: "#/components/parameters/ProjectReferenceId"
    responses:
        201:
          description: "New Training Run created."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrainingRun'
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 201."
        401:
          description: "Unauthorized. Authorization was incorrect."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        404:
          description: Not found. Client_id or project_reference_id are invalid."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
    components:
      tags:
        - name: "training runs"
          description: "Endpoints that deal with training runs- a combination of suggestions (either SigOpt calculated
                        or user supplied) and customer provided results of that suggestions- as first class objects."
      parameters:
        ClientId:
          in: path
          name: client_id
          required: true
          schema:
            type: integer
            minimum: 1
          description: "The id of the client that this training_run is associated with."
        ProjectReferenceId:
          in: path
          name: project_reference_id
          required: true
          schema:
            type: string
            minLength: 1
            maxLength: 32
          description: "The id of the project that this training_run is associated with."
      schemas:
        TrainingRunBase:
          type: object
          required: ["name", "state"]
          properties:
            assignments:
              type: object
              description: "Map of parameter names to their assigned values for the specific training run."
              example: {"a": 1, "b": 2}
            assignments_meta:
              type: object
              description: "Map of parameter names to metadata for the associated assignment. There must be a matching
                            of variable names to key names in the assignments map. The values of each key must be an
                            object with a field named source. The value of that source field must be present as a key
                            the assignments_sources map."
              example: {"a": {"source": "source1"}, "b": {"source": "source2"}}
              additionalProperties:
                type: object
                required: ["source"]
                properties:
                  source:
                    type: string
                    description: "String name that must be a key in the assignments_sources map."
            assignments_sources:
              description: "Map of assignment source names to metadata for the associated source. There must be a key
                            for every value of 'source' in the assignments_meta objects."
              type: object
              additionalProperties:
                required: ["default_show", "sort"]
                properties:
                  default_show:
                    type: boolean
                    description: "If true, show the source in the UI by default."
                  sort:
                    type: number
                    minimum : 1
                    description: "Ordered rank of sources to be sort keys for display. So the most important row of
                                  data should be ranked 1, then the next as 2, etc."
                type: object
              example: {"source1": {"default_show": True, "sort": 1}, "source2": {"default_show": False, "sort": 2}}
            datasets:
              type: object
              description: "Key-value store. The key is the natural language description of a dataset used in this
                            experiment run. The value is always an empty object."
              example: {"my_image_dataset": {}}
            deleted:
              type: boolean
              description: "If true, this run is soft-deleted and won't be visible in the UI by default. Can be
                            viewed if explicitly searched for, and then recovered by setting this to false again."
              default: False
            favorite:
              type: boolean
              description: "If true, this run has been favorited by the user. Displayed in UI."
            logs:
              type: object
              description: "The logs generated by the experimental run, if the experimenter wants to keep them."
              additionalProperties:
                type: object
                properties:
                  content:
                    type: string
                    maxLength: 1124
                    description: "A chunk of logs data. If longer than chunk is submitted, server truncates in the
                                  middle, with ellipsis to mark truncation."
                example: {"evaluator":{"content": "This is the log of the evaluation step."}}
            metadata:
              type: object
              description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                            strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                            client side."
            model:
              type: object
              description: "Information about the model used."
              properties:
                type:
                  type: string
                  description: "Natural Language description of the type of model used for this run."
              example: {"type":"xgboost"}
            name:
              type: string
              description: "Human friendly name of this training run."
              minLength: 1
              maxLength: 100
            source_code:
              type: object
              description: "Information about the source code used to generate or evaluate this run."
              properties:
                content:
                  type: string
                  description: |
                    The source code contents in plain text. This can be the program entrypoint or notebook
                    cell.
                hash:
                  type: string
                  description: "githash of the version of the code used to generate or evaluate this run."
            state:
              type: string
              enum: ["active", "completed", "failed"]
              description: "Current state of training run."
            values:
              type: object
              description: "Map containing the results of the experiment. Keys are the metric names. Values are
                            objects with two values, value and value_stddev."
              additionalProperties:
                type: object
                required: ["value"]
                properties:
                  value:
                    type: number
                    description: "Actual value of this metric name."
                  value_stddev:
                    type: number
                    description: "Standard deviation of this metric result."
            dev_metadata:
                  type: object
                  description: "Optional internal provided set of key-value pairs, used for tracking on server side.
                                This is reserved for SigOpt use."
            sys_metadata:
              type: object
              description: "Optional information for storing information for various integrations. If using, e.g.
                            xgboost, you might want to store information about how it is set up in this field, for
                            later retrieval and display."
              properties:
                feature_importances:
                  type: object
                  description: "Information about the feature importances of this run."
                  properties:
                    scores:
                      type: array
                      items:
                        type: string
                        maxLength: 100
                      maxItems: 50
                      description: "Information about the feature to feature score relationship."
                    type:
                      type: string
                      description: "Type of feature importance"
        TrainingRun:
          allOf:
            - $ref: "#/components/schemas/TrainingRunBase"
            - type: object
              description: "An object that combines all the information about a single cycle of model training and
                            evaluation, including input assignments and results."
              properties:
                project:
                  type: string
                  minLength: 1
                  maxLength: 32
                  description: "The id of the project that this training_run is associated with."
                id:
                  type: integer
                  minimum: 1
                  description: "The unique id of this training_run."
                finished:
                  type: boolean
                  description: "If true, the training_run is done, with no more work necessary."
                created:
                  type: integer
                  description: "Epoch time that this training_run was created."
                updated:
                  type: integer
                  description: "Epoch time that this training_run was last updated."
                checkpoint_count:
                  type: integer
                  description: "Number of checkpoints in this training_run."
                client:
                  type: integer
                  minimum: 1
                  description: "The id of the client that this training_run is associated with."
                completed:
                  type: integer
                  description: "Epoch time that this training_run was completed, if finished. Otherwise null."
                experiment:
                  type: integer
                  minimum: 1
                  description: "The id of the experiment that this training_run is associated with, if any."
                user:
                  type: integer
                  minimum: 1
                  description: "The id of the user who created this training_run, if any."
                tags:
                  type: array
                  items:
                    type: integer
                    minimum: 1
                    description: "The id of a user defined and associated tag with this training_run."
                files:
                  type: array
                  items:
                    type: integer
                    minimum: 1
                    description: "The id of a user uploaded file associated with this training_run."

        TrainingRunPost:
          allOf:
            - $ref: "#/components/schemas/TrainingRunBase"
    """

  authenticator = api_token_authentication

  def handle(self, params):
    return self.handle_batch([params])[0]

  def handle_batch(self, batch):
    client = self.client
    project = self.project

    runs = []
    for params in batch:
      training_run_data = params.training_run_params.training_run_data
      reported_state = self.get_validated_reported_state(training_run_data)
      training_run_data.state = reported_state

      training_run = TrainingRun(
        client_id=client.id,
        created_by=napply(self.auth.current_user, lambda u: u.id),
        project_id=project.id,
        training_run_data=training_run_data,
      )
      runs.append(training_run)

    self.services.training_run_service.insert_training_runs(runs)

    return [
      TrainingRunJsonBuilder(
        training_run=training_run,
        checkpoint_count=0,
        project=project,
      )
      for training_run in runs
    ]


class ProjectsTrainingRunsBatchCreateHandler(ProjectsTrainingRunsCreateHandler):
  """Creates a large set of training_runs at once.
    This endpoint allows bulk creation of training_runs. This bulk update is transactional, in the sense that either it
    will complete for all training_runs in the array or none will be added.

    Note that attribution of errors is very tricky with this endpoint. A 400 error means that at least one new
    training_run failed validation, but there is no way to map that error to a specific training_run request based on
    server response- it is the caller's responsibility to find the cause of the error.

    Individual accounts might have lower numbers of individual training_runs allowed in a single transaction, depending
    on account type and server load factors. The listed maxLength here is just the largest allowed across the entire
    system. A 400 error with message will be returned if you exceed the maxLength for your account.
    ---
    tags:
      - "training runs"
    requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: "#/components/schemas/TrainingRunPost"
              maxLength: 10000
              minLength: 1
    parameters:
      - $ref: "#/components/parameters/ClientId"
      - $ref: "#/components/parameters/ProjectReferenceId"
    responses:
        201:
          description: "New Training Runs created."
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TrainingRun'
                maxLength: 10000
                minLength: 1
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 201."
        401:
          description: "Unauthorized. Authorization was incorrect for at least one new training_run."
        400:
          description: "Bad Request Format. Failed validation of some kind for at least one new training_run."
        404:
          description: Not found. Client_id or project_reference_id are invalid for at least one new training_run."
        429:
          description: "Client has engaged too many events recently and is rate limited. This is only counted as
                        one event, as far as throttling is concerned, no matter how many training_runs are created."
        5XX:
          description: "Unexpected Error"
    """

  class DummyRequest(object):
    def __init__(self, params):
      self._params = params

    def params(self):
      return self._params

  def parse_params(self, request):
    runs = request.params().get("runs", [])
    max_count = get_default_max_batch_runs(self.services)
    if len(runs) > max_count:
      raise BadParamError(
        f"The number of runs needs to be less than or equal to {max_count}. "
        f"Please consider separating your {len(runs)} runs into multiple batches."
      )
    return [self.parse_request(self.DummyRequest(run)) for run in runs]

  def handle(self, params):
    return PaginationJsonBuilder(data=self.handle_batch(params))
