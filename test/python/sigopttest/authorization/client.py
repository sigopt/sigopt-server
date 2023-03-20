# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from mock import Mock

from zigopt.authorization.client import ClientAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE

from sigopttest.authorization.test_base import _TestAuthorizationCore


class TestClientAuthorization(_TestAuthorizationCore):
  def test_client(self, services):
    client_token = Mock(
      all_experiments=True,
      guest_can_read=True,
      guest_can_write=True,
      guest_experiment_id=None,
      client_id=self.client_id,
    )
    auth = ClientAuthorization(
      current_client=Mock(id=self.client_id, organization_id=self.organization_id), client_token=client_token
    )

    assert auth.current_client.id == self.client_id
    assert auth.current_user is None
    assert auth.api_token == client_token
    assert not auth.can_act_on_user(services, READ, self.user)
    assert not auth.can_act_on_user(services, WRITE, self.user)
    assert not auth.can_act_on_user(services, ADMIN, self.user)
    assert not auth.can_act_on_user(services, READ, self.other_user)
    assert not auth.can_act_on_user(services, WRITE, self.other_user)
    assert not auth.can_act_on_user(services, ADMIN, self.other_user)
    assert auth.can_act_on_client(services, READ, self.client)
    assert auth.can_act_on_client(services, WRITE, self.client)
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
    assert auth.can_act_on_experiment(services, WRITE, self.experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.experiment)
    assert not auth.can_act_on_experiment(services, READ, self.other_experiment)
    assert not auth.can_act_on_experiment(services, WRITE, self.other_experiment)
    assert not auth.can_act_on_experiment(services, ADMIN, self.other_experiment)
    assert auth.can_act_on_experiment(services, READ, self.another_experiment_with_client)
    assert auth.can_act_on_experiment(services, WRITE, self.another_experiment_with_client)
    assert not auth.can_act_on_experiment(services, ADMIN, self.another_experiment_with_client)
    assert auth.can_act_on_project(services, READ, self.project)
    assert auth.can_act_on_project(services, WRITE, self.project)
    assert not auth.can_act_on_project(services, ADMIN, self.project)
    assert not auth.can_act_on_project(services, READ, self.other_project)
    assert not auth.can_act_on_project(services, WRITE, self.other_project)
    assert not auth.can_act_on_project(services, ADMIN, self.other_project)
    assert auth.can_act_on_project(services, READ, self.another_project_with_client)
    assert auth.can_act_on_project(services, WRITE, self.another_project_with_client)
    assert not auth.can_act_on_project(services, ADMIN, self.another_project_with_client)
