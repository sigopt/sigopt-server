# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestListExperimentsDelete(ExperimentsTestBase):
  def test_experiment_list_deleted(self, connection):
    connection.create_any_experiment()
    connection.create_any_experiment()
    e3 = connection.create_any_experiment()
    connection.experiments(e3.id).delete()

    assert len(connection.clients(connection.client_id).experiments().fetch().data) == 2
    assert connection.clients(connection.client_id).experiments().fetch().count == 2
    assert len(connection.clients(connection.client_id).experiments().fetch(state="active").data) == 2
    assert connection.clients(connection.client_id).experiments().fetch(state="active").count == 2
    assert len(connection.clients(connection.client_id).experiments().fetch(state="deleted").data) == 1
    assert connection.clients(connection.client_id).experiments().fetch(state="deleted").count == 1
    assert len(connection.clients(connection.client_id).experiments().fetch(state="all").data) == 3
    assert connection.clients(connection.client_id).experiments().fetch(state="all").count == 3
