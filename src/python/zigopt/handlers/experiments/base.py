# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from flask import request

from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.json.builder import ExperimentJsonBuilder
from zigopt.net.errors import BadParamError, ForbiddenError, NotFoundError, RedirectException
from zigopt.protobuf.gen.token.tokenmeta_pb2 import TokenMeta


def maybe_raise_for_incorrect_development_access(auth, experiment, docs_url):
  if auth.developer and (auth.development != experiment.development):
    experiment_type = "development" if experiment.development else "production"
    provided_token_type = "a development" if auth.development else "an api"
    required_token_type = "api" if auth.development else "development"
    raise ForbiddenError(
      f"Attempting to access {experiment_type} experiment {experiment.id} with {provided_token_type} token."
      f" Please reauthenticate with your {required_token_type} token and try again."
      f" See {docs_url}/overview/authentication for more information."
    )


OBSERVATION_BUDGET_KEY = "observation_budget"
BUDGET_KEY = "budget"


def get_budget_key(runs_only):
  if runs_only:
    return BUDGET_KEY
  return OBSERVATION_BUDGET_KEY


def get_budget_param(json_dict, runs_only, return_key=False):
  if runs_only:
    key = BUDGET_KEY
    if OBSERVATION_BUDGET_KEY in json_dict:
      raise BadParamError(f"{OBSERVATION_BUDGET_KEY} is no longer a valid field, please use {BUDGET_KEY} instead.")
  else:
    key = OBSERVATION_BUDGET_KEY
    if BUDGET_KEY in json_dict:
      raise BadParamError(f"{BUDGET_KEY} is not a valid field.")
  budget = get_with_validation(json_dict, key, ValidationType.positive_integer)
  if return_key:
    return budget, key
  return budget


class ExperimentHandler(Handler):
  allow_development = True
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SHARED_EXPERIMENT_SCOPE)
  JsonBuilder = ExperimentJsonBuilder
  redirect_ai_experiments = False

  def __init__(self, services, request, experiment_id):
    if experiment_id is None:
      raise Exception("Experiment id required")

    self.client = None
    self.experiment_id = experiment_id
    self.experiment = None
    super().__init__(services, request)

  def prepare(self):
    super().prepare()
    if self.redirect_ai_experiments and self.experiment.runs_only:
      raise RedirectException(request.path.replace("/experiments/", "/aiexperiments/"))
    app_url = self.services.config_broker["address.app_url"]
    docs_url = app_url + "/docs"
    maybe_raise_for_incorrect_development_access(auth=self.auth, experiment=self.experiment, docs_url=docs_url)

  def find_objects(self):
    experiment = self._find_experiment(self.experiment_id)
    return extend_dict(
      super().find_objects(),
      {
        "client": self.services.client_service.find_by_id(
          experiment.client_id, current_client=self.auth.current_client
        ),
        "experiment": experiment,
      },
    )

  def _find_experiment(self, experiment_id):
    if experiment_id:
      experiment = self.services.experiment_service.find_by_id(
        experiment_id,
        include_deleted=True,
      )
      if experiment:
        return experiment
    raise NotFoundError(f"No experiment {experiment_id}")

  def can_act_on_objects(self, requested_permission, objects):
    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_experiment(
      self.services, requested_permission, objects["experiment"]
    )

  def _reset_hyperparameters(self):
    self.services.aux_service.reset_hyperparameters(self.experiment)
    num_observations = self.services.observation_service.count_by_experiment(self.experiment)
    self.services.optimize_queue_service.enqueue_optimization(
      self.experiment,
      force=True,
      num_observations=num_observations,
    )
