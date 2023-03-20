# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.authorization.guest import GuestAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE

from sigopttest.authorization.test_base import _TestAuthorizationCore


class TestGuestAuthorization(_TestAuthorizationCore):
  training_run = Mock(
    id=next(_TestAuthorizationCore.ids),
    experiment_id=_TestAuthorizationCore.experiment.id,
    client_id=_TestAuthorizationCore.client_id,
    project_id=_TestAuthorizationCore.project.id,
  )

  training_run_no_experiment = Mock(
    id=next(_TestAuthorizationCore.ids),
    experiment_id=None,
    client_id=_TestAuthorizationCore.client_id,
    project_id=_TestAuthorizationCore.project.id,
  )

  training_run_other_client = Mock(
    id=next(_TestAuthorizationCore.ids),
    experiment_id=_TestAuthorizationCore.other_experiment.id,
    client_id=_TestAuthorizationCore.other_client_id,
  )

  @pytest.fixture
  def services(self):
    services = self.make_services()

    def dummy_find_training_run_by_id(training_run_id):
      for tr in (self.training_run, self.training_run_no_experiment, self.training_run_other_client):
        if tr.id == training_run_id:
          return tr
      return None

    services.training_run_service = Mock(find_by_id=dummy_find_training_run_by_id)
    return services

  def test_guest_no_experiment(self, services):
    auth = GuestAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id),
      client_token=Mock(
        all_experiments=False,
        guest_can_read=True,
        guest_can_write=False,
        guest_experiment_id=None,
        guest_training_run_id=None,
        client_id=self.client_id,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user is None
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert not auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)
    assert auth.can_act_on_organization(services, READ, self.organization)
    assert not auth.can_act_on_organization(services, WRITE, self.organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)
    assert not auth.can_act_on_experiment(services, READ, self.experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_project(services, READ, self.project)
    assert not auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_training_run(services, READ, self.training_run)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_other_client)

  def test_guest_single_experiment(self, services):
    auth = GuestAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id),
      client_token=Mock(
        all_experiments=False,
        guest_can_read=True,
        guest_can_write=False,
        guest_experiment_id=self.experiment.id,
        guest_training_run_id=None,
        client_id=self.client_id,
      ),
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user is None
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert not auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)
    assert auth.can_act_on_organization(services, READ, self.organization)
    assert not auth.can_act_on_organization(services, WRITE, self.organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)
    assert auth.can_act_on_experiment(services, READ, self.experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert auth.can_act_on_project(services, READ, self.project)
    assert not auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert not auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert not auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert auth.can_act_on_training_run(services, READ, self.training_run)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_other_client)

  def test_guest_single_training_run_experiment(self, services):
    auth = GuestAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id),
      client_token=Mock(
        all_experiments=False,
        guest_can_read=True,
        guest_can_write=False,
        guest_experiment_id=self.experiment.id,
        guest_training_run_id=self.training_run.id,
        client_id=self.client_id,
      ),
    )
    assert auth.current_client.id == self.client_id
    assert auth.current_user is None
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert not auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)
    assert auth.can_act_on_organization(services, READ, self.organization)
    assert not auth.can_act_on_organization(services, WRITE, self.organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)
    assert auth.can_act_on_experiment(services, READ, self.experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert auth.can_act_on_project(services, READ, self.project)
    assert not auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert not auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert not auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert auth.can_act_on_training_run(services, READ, self.training_run)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_other_client)

  def test_guest_single_training_run_no_experiment(self, services):
    auth = GuestAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id),
      client_token=Mock(
        all_experiments=False,
        guest_can_read=True,
        guest_can_write=False,
        guest_experiment_id=None,
        guest_training_run_id=self.training_run_no_experiment.id,
        client_id=self.client_id,
      ),
    )
    assert auth.current_client.id == self.client_id
    assert auth.current_user is None
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert not auth.can_act_on_client(services, WRITE, self.client)
    assert not auth.can_act_on_client(services, ADMIN, self.client)
    assert not auth.can_act_on_client(services, READ, self.other_client)
    assert not auth.can_act_on_client(services, WRITE, self.other_client)
    assert not auth.can_act_on_client(services, ADMIN, self.other_client)
    assert auth.can_act_on_organization(services, READ, self.organization)
    assert not auth.can_act_on_organization(services, WRITE, self.organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.organization)
    assert not auth.can_act_on_organization(services, READ, self.other_organization)
    assert not auth.can_act_on_organization(services, WRITE, self.other_organization)
    assert not auth.can_act_on_organization(services, ADMIN, self.other_organization)
    assert not auth.can_act_on_experiment(services, READ, self.experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert not auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert auth.can_act_on_project(services, READ, self.project)
    assert not auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert not auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert not auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
    assert not auth.can_act_on_training_run(services, READ, self.training_run)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run)
    assert auth.can_act_on_training_run(services, READ, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_no_experiment)
    assert not auth.can_act_on_training_run(services, READ, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, WRITE, self.training_run_other_client)
    assert not auth.can_act_on_training_run(services, ADMIN, self.training_run_other_client)
