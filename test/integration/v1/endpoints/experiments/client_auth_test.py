# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.experiments_test_base import ExperimentsTestBase


# These tests should raise no status and will fail if any authentication errors are encountered
class TestExperimentClientAuthorization(ExperimentsTestBase):
  def test_create_experiment_without_client(self, connection):
    connection.as_client_only().create_any_experiment()

  def test_create_experiment_for_client(self, connection, client_id):
    connection.as_client_only().create_any_experiment(client_id=client_id)

  def test_detail_experiments_without_client(self, connection):
    connection.as_client_only().experiments().fetch()

  def test_detail_experiments_for_client(self, connection):
    client_id = connection.client_id
    connection.as_client_only().clients(client_id).experiments().fetch()

  def test_detail_user_experiments(self, connection):
    connection.as_client_only().users(connection.user_id).experiments().fetch()
