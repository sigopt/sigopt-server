# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from integration.base import RaisesApiException
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentUserAuthorization(ExperimentsTestBase):
  def test_create_experiment_without_client(self, connection, any_meta):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.experiments().create(**any_meta)

  def test_detail_experiments_without_client(self, connection):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.experiments().fetch()

  def test_detail_user_experiments(self, connection):
    connection.users(connection.user_id).experiments().fetch()
