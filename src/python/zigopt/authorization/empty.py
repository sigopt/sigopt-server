# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.token.model import Token


class EmptyAuthorization:
  @property
  def current_client(self):
    return None

  @property
  def current_user(self):
    return None

  @property
  def api_token(self) -> Token | None:
    return None

  @property
  def development(self):
    return False

  @property
  def developer(self):
    return False

  def can_act_on_user(self, services, requested_permission, user):
    return False

  def can_act_on_client(self, services, requested_permission, client):
    return False

  def can_act_on_organization(self, services, requested_permission, organization):
    return False

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    return False

  def can_act_on_experiment(self, services, requested_permission, experiment):
    if experiment is None:
      return False
    return self._can_act_on_client_artifacts(
      services=services,
      requested_permission=requested_permission,
      client_id=experiment.client_id,
      owner_id_for_artifacts=experiment.created_by,
    )

  def can_act_on_project(self, services, requested_permission, project):
    if project is None:
      return False
    return self._can_act_on_client_artifacts(
      services=services,
      requested_permission=requested_permission,
      client_id=project.client_id,
      owner_id_for_artifacts=project.created_by,
    )

  def can_act_on_training_run(self, services, requested_permission, training_run):
    assert training_run.client_id is not None, "Training run must have client_id to check can act on Training run"
    return self._can_act_on_client_artifacts(
      services=services,
      requested_permission=requested_permission,
      client_id=training_run.client_id,
      owner_id_for_artifacts=training_run.created_by,
    )

  def can_act_on_file(self, services, requested_permission, file_obj, client=None):
    if client is None:
      client = services.client_service.find_by_id(file_obj.client_id, include_deleted=True)
    else:
      assert client.id == file_obj.client_id
    return bool(client) and self.can_act_on_client(services, requested_permission, client)

  def filter_can_act_on_experiments(self, services, requested_permission, experiments):
    return [e for e in experiments if self.can_act_on_experiment(services, requested_permission, e)]

  def can_act_on_token(self, services, requested_permission, token):
    return False

  @property
  def authenticated_from_email_link(self):
    return False

  @property
  def session_expiration(self):
    return napply(self.api_token, lambda u: u.expiration_timestamp)
