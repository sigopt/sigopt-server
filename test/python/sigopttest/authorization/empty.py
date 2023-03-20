# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE

from sigopttest.authorization.test_base import _TestAuthorizationCore


class TestEmptyAuthorization(_TestAuthorizationCore):
  def test_all(self, services):
    auth = EmptyAuthorization()
    assert auth.current_client is None
    assert auth.current_user is None
    assert not auth.can_act_on_user(services, NONE, self.user)
    assert not auth.can_act_on_client(services, NONE, self.client)
    assert not auth.can_act_on_organization(services, NONE, self.organization)
    assert not auth.can_act_on_experiment(services, NONE, self.experiment)
    assert not auth.can_act_on_token(services, NONE, self.token)
