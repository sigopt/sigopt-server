# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Iterable

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.experiment.model import Experiment
from zigopt.file.model import File
from zigopt.organization.model import Organization
from zigopt.project.model import Project
from zigopt.token.model import Token
from zigopt.training_run.model import TrainingRun
from zigopt.user.model import User


class Authorization:
  @property
  def current_client(self) -> Client | None:
    raise NotImplementedError()

  @property
  def current_user(self) -> User | None:
    raise NotImplementedError()

  @property
  def api_token(self) -> Token | None:
    raise NotImplementedError()

  @property
  def development(self) -> bool:
    raise NotImplementedError()

  @property
  def developer(self) -> bool:
    raise NotImplementedError()

  def can_act_on_user(self, services, requested_permission: int, user: User) -> bool:
    raise NotImplementedError()

  def can_act_on_client(self, services, requested_permission: int, client: Client) -> bool:
    raise NotImplementedError()

  def can_act_on_organization(self, services, requested_permission: int, organization: Organization) -> bool:
    raise NotImplementedError()

  def _can_act_on_client_artifacts(
    self,
    services,
    requested_permission: int,
    client_id: int,
    owner_id_for_artifacts: int,
  ) -> bool:
    raise NotImplementedError()

  def can_act_on_experiment(self, services, requested_permission: int, experiment: Experiment) -> bool:
    raise NotImplementedError()

  def can_act_on_project(self, services, requested_permission: int, project: Project) -> bool:
    raise NotImplementedError()

  def can_act_on_training_run(self, services, requested_permission: int, training_run: TrainingRun) -> bool:
    raise NotImplementedError()

  def can_act_on_file(self, services, requested_permission, file_obj: File, client: Client | None = None) -> bool:
    raise NotImplementedError()

  def filter_can_act_on_experiments(
    self,
    services,
    requested_permission: int,
    experiments: Iterable[Experiment],
  ) -> bool:
    raise NotImplementedError()

  def can_act_on_token(self, services, requested_permission: int, token: Token) -> bool:
    raise NotImplementedError()

  @property
  def authenticated_from_email_link(self) -> bool:
    raise NotImplementedError()

  @property
  def session_expiration(self) -> int | None:
    raise NotImplementedError()
