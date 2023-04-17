# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Handler and validation for client-reported experiment observations."""
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.handlers.validate.observation import validate_observation_json_dict_for_create
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.json.builder import ObservationJsonBuilder, PaginationJsonBuilder
from zigopt.net.errors import BadParamError, ForbiddenError
from zigopt.observation.data import create_observation_data
from zigopt.observation.from_json import set_observation_data_assignments_task_from_json
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from libsigopt.aux.errors import InvalidKeyError, SigoptValidationError


DEFAULT_MAX_OBSERVATIONS_CREATE_COUNT = 2500


def get_default_max_observations(services):
  return services.config_broker.get(
    "features.maxObservationsCreateCount",
    DEFAULT_MAX_OBSERVATIONS_CREATE_COUNT,
  )


class CreatesObservationsMixin:
  def observation_from_json(
    self,
    json_dict,
    observation,
    observation_data,
    timestamp,
    observation_data_create_update_handler=create_observation_data,
    assignments_handler=set_observation_data_assignments_task_from_json,
  ):
    failed = get_opt_with_validation(json_dict, "failed", ValidationType.boolean)
    values = get_opt_with_validation(json_dict, "values", ValidationType.array)
    suggestion_id = get_opt_with_validation(json_dict, "suggestion", ValidationType.id)
    suggestion = napply(suggestion_id, self.services.suggestion_service.find_by_id)

    if failed is None:
      if observation.reported_failure and not values:
        failed = True

    observation_data_create_update_handler(
      observation_data=observation_data,
      values=values,
      observation=observation,
      experiment=self.experiment,
      failed=failed,
    )

    if timestamp is not None:
      observation_data.timestamp = timestamp
    elif observation.timestamp:
      observation_data.timestamp = observation.timestamp

    client_provided_data = BaseExperimentsCreateHandler.get_client_provided_data(
      json_dict, default=observation.client_provided_data
    )
    if client_provided_data is not None:
      observation_data.client_provided_data = client_provided_data
    else:
      if observation_data.HasField("client_provided_data"):
        observation_data.ClearField("client_provided_data")

    assignments_handler(
      observation_data,
      observation,
      json_dict,
      experiment=self.experiment,
      suggestion=suggestion,
    )

  def create_observation(self, json_dict, timestamp):
    validate_observation_json_dict_for_create(json_dict, self.experiment)
    observation = Observation(experiment_id=self.experiment.id)
    observation_data = ObservationData()

    self.observation_from_json(
      json_dict=json_dict,
      timestamp=timestamp,
      observation=observation,
      observation_data=observation_data,
      observation_data_create_update_handler=create_observation_data,
    )

    observation.data = observation_data
    return observation

  def enqueue_optimization(self, num_observations_before, num_failures_before, new_observations):
    num_observations = num_observations_before + len(new_observations)
    num_failures = num_failures_before + len([o for o in new_observations if o.reported_failure])
    source = self.services.optimizer.get_inferred_optimization_source(
      self.experiment,
      num_observations,
    )
    self.services.observation_service.optimize(
      self.experiment,
      num_observations=num_observations,
      should_enqueue_hyper_opt=source.should_execute_hyper_opt(
        num_successful_observations=num_observations - num_failures,
      ),
    )

  def add_observations(self, observations, client, counts, optimize=True):
    self.services.observation_service.insert_observations(self.experiment, observations)

    if optimize:
      self.enqueue_optimization(
        num_observations_before=counts.observation_count,
        num_failures_before=counts.failure_count,
        new_observations=observations,
      )


class ObservationsCreateHandler(CreatesObservationsMixin, ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    return request

  def handle(self, request):
    if self.experiment.deleted:
      raise SigoptValidationError(f"Cannot create observations for deleted experiment {self.experiment.id}")

    if self.experiment.runs_only:
      raise ForbiddenError(
        f"Observations cannot be created directly for experiment {self.experiment.id}, please create runs instead"
      )

    now = current_datetime()
    client = self.services.client_service.find_by_id(self.experiment.client_id, current_client=self.auth.current_client)
    counts = self.services.observation_service.get_observation_counts(self.experiment.id)
    params = request.params()

    observation_json = dict(
      failed=self.get_failed_for_observation_json(params),
      values=self.get_values_for_observation_json(params),
      suggestion=self.get_suggestion_id_for_observation_json(params),
      metadata=self.get_metadata_for_observation_json(params),
      assignments=self.get_assignments_for_observation_json(params),
      value=self.get_value_for_observation_json(params),
      value_stddev=self.get_value_stddev_for_observation_json(params),
      task=self.get_task_for_observation_create(params),
      no_optimize=self.get_no_optimize_for_observation_json(params),
    )

    bad_keys = params.keys() - observation_json.keys()
    if bad_keys:
      raise InvalidKeyError(f"Unknown keys were provided for observation create: {bad_keys}")

    observation_json = remove_nones(observation_json)

    new_observation = self.create_observation(json_dict=observation_json, timestamp=datetime_to_seconds(now))
    no_optimize = get_opt_with_validation(params, "no_optimize", ValidationType.boolean) or False
    self.add_observations([new_observation], client, counts, no_optimize is not True)

    self.services.experiment_service.mark_as_updated(self.experiment, now)

    return ObservationJsonBuilder(self.experiment, new_observation)

  def get_failed_for_observation_json(self, params):
    return get_opt_with_validation(params, "failed", ValidationType.boolean)

  def get_values_for_observation_json(self, params):
    return get_opt_with_validation(params, "values", ValidationType.arrayOf(ValidationType.object))

  def get_suggestion_id_for_observation_json(self, params):
    return get_opt_with_validation(params, "suggestion", ValidationType.id)

  def get_metadata_for_observation_json(self, params):
    return get_opt_with_validation(params, "metadata", ValidationType.object)

  def get_assignments_for_observation_json(self, params):
    return get_opt_with_validation(params, "assignments", ValidationType.object)

  def get_value_for_observation_json(self, params):
    return get_opt_with_validation(params, "value", ValidationType.number)

  def get_value_stddev_for_observation_json(self, params):
    return get_opt_with_validation(params, "value_stddev", ValidationType.number)

  def get_task_for_observation_create(self, params):
    return get_opt_with_validation(params, "task", ValidationType.oneOf([ValidationType.object, ValidationType.string]))

  def get_no_optimize_for_observation_json(self, params):
    return get_opt_with_validation(params, "no_optimize", ValidationType.boolean)


class ObservationsCreateMultiHandler(CreatesObservationsMixin, ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct(
    "Params",
    (
      "observations",
      "dry_run",
      "no_optimize",
    ),
  )

  def parse_params(self, request):
    data = request.params()
    return self.Params(
      observations=get_with_validation(data, "observations", ValidationType.arrayOf(ValidationType.object)),
      dry_run=get_opt_with_validation(data, "dry_run", ValidationType.boolean) or False,
      no_optimize=get_opt_with_validation(data, "no_optimize", ValidationType.boolean) or False,
    )

  def handle(self, params):
    observations = params.observations

    if self.experiment.deleted:
      raise SigoptValidationError(f"Cannot create observations for deleted experiment {self.experiment.id}")

    max_observations = get_default_max_observations(self.services)
    if len(observations) > max_observations:
      raise SigoptValidationError(
        f"You cannot upload more than {max_observations} observations at once."
        " Please separate your observations into multiple API calls."
      )

    now = current_datetime()
    new_observations = []
    if len(observations) > 0:
      stats = self.services.observation_service.get_observation_counts(self.experiment.id)
      num_failures_before = stats.failure_count
      num_observations_before = stats.observation_count

      for index, data in enumerate(observations):
        validate_observation_json_dict_for_create(data, self.experiment)
        try:
          obs = self.create_observation(
            json_dict=data,
            timestamp=datetime_to_seconds(now),
          )
        except (BadParamError, SigoptValidationError) as e:
          # Add more information to the message
          message = e.args[0]
          message = f"Error in observation {index+1}/{len(observations)}: {message}"
          e.args = (message,) + e.args[1:]
          raise SigoptValidationError(e) from e
        new_observations.append(obs)

      if not params.dry_run:
        self.services.observation_service.insert_observations(self.experiment, new_observations)
        self.services.experiment_service.mark_as_updated(self.experiment, now)
        no_optimize = params.no_optimize or all(
          (get_opt_with_validation(data, "no_optimize", ValidationType.boolean) for data in observations)
        )
        if no_optimize is not True:
          self.enqueue_optimization(
            num_observations_before=num_observations_before,
            num_failures_before=num_failures_before,
            new_observations=new_observations,
          )

    return PaginationJsonBuilder(
      data=[ObservationJsonBuilder(self.experiment, observation) for observation in new_observations],
    )
