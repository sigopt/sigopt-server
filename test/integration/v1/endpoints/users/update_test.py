# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.test_base import V1Base


class TestUserUpdate(V1Base):
  def test_update(self, connection, config_broker):
    user = connection.users(connection.user_id).fetch()
    name = user.name
    updated_name = name + " updated"
    update_response = connection.users(connection.user_id).update(name=updated_name)
    assert update_response.name == updated_name
    updated_user = connection.users(connection.user_id).fetch()
    assert updated_user.name == updated_name
