# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.db.column import JsonPath, jsonb_set, jsonb_strip_nulls, unwind_json_path
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.experiments.base import maybe_raise_for_incorrect_development_access
from zigopt.handlers.training_runs.utils import get_json_paths_and_values
from zigopt.net.errors import NotFoundError
from zigopt.project.model import Project
from zigopt.protobuf.gen.token.tokenmeta_pb2 import TokenMeta
from zigopt.training_run.model import TrainingRun


class TrainingRunHandler(Handler):
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SHARED_EXPERIMENT_SCOPE)
  allow_development = True

  training_run: TrainingRun | None
  project: Project | None

  def __init__(self, services, request, *, training_run_id, experiment_id=None):
    super().__init__(services, request)
    if training_run_id is None:
      raise Exception("Training Run id required")
    self.training_run_id = training_run_id
    self.experiment_id = experiment_id
    self.client = None
    self.experiment = None
    self.training_run = None
    self.project = None

  def prepare(self):
    super().prepare()
    if self.experiment:
      app_url = self.services.config_broker["address.app_url"]
      docs_url = app_url + "/docs"
      maybe_raise_for_incorrect_development_access(auth=self.auth, experiment=self.experiment, docs_url=docs_url)

  def find_objects(self):
    training_run = self._find_training_run(self.training_run_id)
    project = self._find_project(training_run.project_id, training_run.client_id, training_run.id)
    client = self._find_client(training_run.client_id)
    experiment = self._maybe_find_experiment(self.experiment_id)
    return extend_dict(
      super().find_objects(),
      remove_nones_mapping(
        {
          "client": client,
          "experiment": experiment,
          "training_run": training_run,
          "project": project,
        }
      ),
    )

  def _maybe_find_experiment(self, experiment_id):
    if experiment_id:
      experiment = self.services.experiment_service.find_by_id(
        experiment_id,
        include_deleted=True,
      )
      if experiment:
        return experiment
      raise NotFoundError(f"No experiment {experiment_id}")
    return None

  def _find_training_run(self, training_run_id):
    training_run = self.services.training_run_service.find_by_id(training_run_id)
    if training_run:
      return training_run
    raise NotFoundError(f"Training run {training_run_id} not found")

  def _find_client(self, client_id):
    client = self.services.client_service.find_by_id(client_id)
    if client:
      return client
    raise NotFoundError(f"Client {client_id} not found")

  def _find_project(self, project_id, client_id, training_run_id):
    if project_id is None:
      raise NotFoundError(f"Training run {training_run_id} not found")
    project = self.services.project_service.find_by_client_and_id(client_id, project_id)
    if project is None:
      raise NotFoundError(f"Training run {training_run_id} not found")
    return project

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    training_run = objects["training_run"]
    experiment = objects.get("experiment")
    return (
      super().can_act_on_objects(requested_permission, objects)
      and self.auth.can_act_on_training_run(self.services, requested_permission, training_run)
      and (experiment is None or self.auth.can_act_on_experiment(self.services, requested_permission, experiment))
      and (experiment is None or training_run.experiment_id == experiment.id)
    )

  def create_update_clause(self, merge_objects, training_run_data_json):
    initial_meta_clause = TrainingRun.training_run_data
    meta_clause = initial_meta_clause
    for k, v in training_run_data_json.items():
      for attribute, clause_value in get_json_paths_and_values(merge_objects, initial_meta_clause[k], v):
        json_path = JsonPath(*unwind_json_path(attribute))
        meta_clause = jsonb_set(meta_clause, json_path, clause_value)
    meta_clause = jsonb_strip_nulls(meta_clause)
    return meta_clause

  def emit_update(self, update_clause):
    assert self.training_run is not None

    return self.services.database_service.update(
      self.services.database_service.query(TrainingRun).filter(TrainingRun.id == self.training_run.id),
      update_clause,
    )
