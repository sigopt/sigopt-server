# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE, READ
from zigopt.training_run.model import TrainingRun


def readonly(func):
  def wrapped(self, services, requested_permission, *args, **kwargs):
    if requested_permission in (READ, NONE):
      return func(self, services, requested_permission, *args, **kwargs)
    return False

  return wrapped


class GuestAuthorization(EmptyAuthorization):
  def __init__(self, current_client, client_token):
    assert client_token.client_id == current_client.id
    super().__init__()
    self._current_client = current_client
    self._client_token = client_token

  @property
  def current_client(self):
    return self._current_client

  @property
  def api_token(self):
    return self._client_token

  @readonly
  def can_act_on_client(self, services, requested_permission, client):
    return self._can_act_on_client_id(services, requested_permission, client.id)

  def _can_act_on_client_id(self, services, requested_permission, client_id):
    return (
      self._client_token.guest_can_read
      and self._current_client.id
      and client_id
      and self._current_client.id == client_id
    )

  @readonly
  def can_act_on_organization(self, services, requested_permission, organization):
    return (
      self._client_token.guest_can_read
      and self._current_client.id
      and organization
      and organization.id
      and self._current_client.organization_id == organization.id
    )

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    assert False, "Should not be called"  # noqa: DEL031
    return False

  @readonly
  def can_act_on_experiment(self, services, requested_permission, experiment):
    return bool(
      experiment
      and self._can_act_on_client_id(services, requested_permission, experiment.client_id)
      and self._client_token.guest_experiment_id
      and self._client_token.guest_experiment_id == experiment.id
    )

  @readonly
  def can_act_on_project(self, services, requested_permission, project):
    experiment: Experiment | None = napply(
      self._client_token.guest_experiment_id, services.experiment_service.find_by_id
    )
    training_run: TrainingRun | None = napply(
      self._client_token.guest_training_run_id, services.training_run_service.find_by_id
    )
    project_ids: Sequence[int] = distinct(
      remove_nones_sequence(
        [
          napply(experiment, lambda e: e.project_id),
          napply(training_run, lambda t: t.project_id),
        ],
      )
    )
    if len(project_ids) != 1:
      return False
    (project_id,) = project_ids
    return bool(
      project
      and project.id
      and self._can_act_on_client_id(self, requested_permission, project.client_id)
      and project_id
      and project_id == project.id
    )

  @readonly
  def can_act_on_training_run(self, services, requested_permission, training_run):
    if training_run and self._can_act_on_client_id(self, requested_permission, training_run.client_id):
      if training_run.experiment_id:
        # NOTE: We don't require a training run match here, because
        #  a) Experiment share tokens need to be able to see all the training runs for that experiment
        #  b) Training run share tokens can click through to the experiment page, and then can also do a)
        return (
          self._client_token.guest_experiment_id
          and self._client_token.guest_experiment_id == training_run.experiment_id
        )
      return self._client_token.guest_training_run_id and self._client_token.guest_training_run_id == training_run.id
    return False

  @readonly
  def can_act_on_token(self, services, requested_permission, token):
    return self._client_token.guest_can_read and token and self._client_token.token == token.token
