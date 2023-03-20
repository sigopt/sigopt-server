# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from http import HTTPStatus

import pytest
from flaky import flaky

from zigopt.optimization_aux.model import ExperimentOptimizationAux

from integration.base import RaisesApiException
from integration.utils.random_assignment import random_assignments
from integration.utils.wait import wait_for
from integration.v1.endpoints.importances.test_base import ExperimentImportancesTestBase


class TestExperimentMetricImportancesUpdate(ExperimentImportancesTestBase):
  @pytest.mark.slow
  @flaky(max_runs=2)
  def test_can_delete(
    self,
    services,
    connection,
    client_id,
    wait_for_empty_optimization_queue,
    read_connection_same_client,
  ):
    e = self.create_experiment_and_observations(connection, client_id, self.experiment_meta)
    wait_for_empty_optimization_queue()

    num_observations = 2
    for _ in range(num_observations):
      assignments = random_assignments(e)
      connection.experiments(e.id).observations().create(
        assignments=assignments,
        values=[{"value": assignments["a"] + assignments["b"]}],
      )

    def get_hyperparameters():
      zigopt_hyperparameters = services.database_service.all(
        services.database_service.query(ExperimentOptimizationAux).filter(
          ExperimentOptimizationAux.experiment_id == e.id
        )
      )
      assert len(zigopt_hyperparameters) >= 1
      return True

    wait_for(get_hyperparameters)

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection_same_client.experiments(e.id).hyperparameters().delete()

    connection.experiments(e.id).hyperparameters().delete()

    def get_no_hyperparameters():
      zigopt_hyperparameters = services.database_service.all(
        services.database_service.query(ExperimentOptimizationAux).filter(
          ExperimentOptimizationAux.experiment_id == e.id
        )
      )
      assert not zigopt_hyperparameters
      return True

    wait_for(get_no_hyperparameters)
