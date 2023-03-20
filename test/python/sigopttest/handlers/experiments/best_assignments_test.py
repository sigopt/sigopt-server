# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.authorization.empty import EmptyAuthorization
from zigopt.handlers.experiments.best_assignments import ExperimentsBestAssignmentsHandler

from sigopttest.optimize.sources.base_test import UnitTestBase


class TestExperimentsBestAssignmentsHandler(UnitTestBase):
  @pytest.fixture(params=["", "constraints", "multisolution"])
  def experiment(self, request):
    return self.create_experiment(request.param)

  def test_handler_calls_get_best_observations(self, experiment):
    observations = [1, 2, 3]
    services = Mock()
    services.observation_service.all_data = Mock(return_value=observations)
    get_best_observations = Mock(return_value=[observations])
    services.experiment_best_observation_service.get_best_observations = get_best_observations

    request = Mock()
    params = Mock(path="/v1/experiments/1/best_observations")

    experiments_best_assignments_handler = ExperimentsBestAssignmentsHandler(services, request, experiment.id)
    experiments_best_assignments_handler.auth = EmptyAuthorization()
    experiments_best_assignments_handler.experiment = experiment

    experiments_best_assignments_handler.handle(params)
    get_best_observations.assert_called_with(experiment, observations)
