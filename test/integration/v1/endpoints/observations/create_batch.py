# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestCreateBatch(V1Base):
  @pytest.fixture
  def experiment(self, connection):
    return connection.create_any_experiment()

  def test_batch_observations_create(self, connection, experiment):
    suggestions = [connection.experiments(experiment.id).suggestions().create() for s in range(10)]
    observations = [dict(suggestion=s.id, values=[{"value": random.random()}], no_optimize=True) for s in suggestions]
    connection.experiments(experiment.id).observations().create_batch(
      observations=observations,
      no_optimize=True,
    )

  def test_batch_observations_create_no_data(self, connection, experiment):
    connection.experiments(experiment.id).observations().create_batch(observations=[])

  def test_invalid_suggestion(self, connection, experiment):
    with connection.create_any_experiment() as other_experiment:
      s = connection.experiments(other_experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(suggestion=s.id, values=[{"value": 1}])
      connection.experiments(other_experiment.id).observations().create(suggestion=s.id, values=[{"value": 1}])
