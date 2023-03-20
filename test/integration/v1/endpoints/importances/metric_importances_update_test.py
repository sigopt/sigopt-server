# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from http import HTTPStatus

import pytest
from flaky import flaky
from sigopt.exception import ApiException

from integration.base import RaisesApiException
from integration.utils.random_assignment import random_assignments
from integration.utils.wait import wait_for
from integration.v1.endpoints.importances.test_base import ExperimentImportancesTestBase


class TestExperimentMetricImportancesUpdate(ExperimentImportancesTestBase):
  @pytest.mark.slow
  @flaky(max_runs=2)
  def test_user_with_write_can_update(
    self, connection, client_id, wait_for_empty_optimization_queue, read_connection_same_client
  ):
    e = self.create_experiment_and_observations(connection, client_id, self.experiment_meta)
    wait_for_empty_optimization_queue()

    num_observations = 5
    for _ in range(num_observations):
      assignments = random_assignments(e)
      connection.experiments(e.id).observations().create(
        assignments=assignments,
        values=[{"value": assignments["a"] + assignments["b"]}],
        no_optimize=True,
      )

    def get_importances():
      try:
        return connection.experiments(e.id).metric_importances().fetch().data[0].importances
      except ApiException:
        return None

    before = wait_for(get_importances)

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection_same_client.experiments(e.id).metric_importances().update()

    connection.experiments(e.id).metric_importances().update()

    def updated_importances():
      after = connection.experiments(e.id).metric_importances().fetch().data[0].importances
      assert before["a"] != after["a"] or before["b"] != after["b"]
      return True

    wait_for(updated_importances)
