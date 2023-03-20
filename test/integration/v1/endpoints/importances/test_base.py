# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.utils.make_values import make_values
from integration.utils.random_assignment import random_assignments
from integration.v1.test_base import V1Base


class ExperimentImportancesTestBase(V1Base):
  experiment_meta = dict(
    name="importances",
    parameters=[
      dict(name="a", type="int", bounds=dict(min=1, max=50)),
      dict(name="b", type="double", bounds=dict(min=-50, max=0)),
      dict(name="g", type="double", bounds=dict(min=50, max=100)),
    ],
  )

  def endpoint(self, connection, experiment):
    raise NotImplementedError()

  @pytest.fixture(
    params=[
      "simple",
      "single_metric_with_name",
      "multimetric",
    ]
  )
  def meta(self, request):
    meta = deepcopy(self.experiment_meta)
    if request.param == "multimetric":
      meta["metrics"] = [
        {
          "name": "metric1",
        },
        {
          "name": "metric2",
        },
      ]
      meta["observation_budget"] = 30
    elif request.param == "single_metric_with_name":
      meta["metrics"] = [
        {
          "name": "single_metric",
        }
      ]
    return meta

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture(autouse=True)
  def ensure_enabled(self, config_broker):
    if not config_broker.get("features.importances", True):
      pytest.skip()

  def create_experiment_and_observations(self, connection, client_id, experiment_meta):
    e = connection.clients(client_id).experiments().create(**experiment_meta)

    num_observations = len(e.parameters) * 5
    for i in range(num_observations):
      assignments = random_assignments(e)

      if experiment_meta.get("metrics"):
        vals = [assignments["a"] + assignments["b"] for _ in range(len(experiment_meta["metrics"]))]
        connection.experiments(e.id).observations().create(
          assignments=assignments,
          values=make_values(e, vals),
          no_optimize=(i < num_observations - 1),
        )
      else:
        connection.experiments(e.id).observations().create(
          assignments=assignments,
          values=[{"value": assignments["a"] + assignments["b"]}],
          no_optimize=(i < num_observations - 1),
        )

    return e

  def base_test_importances_no_observations(self, connection, client_id):
    with connection.create_any_experiment() as e:
      with RaisesApiException(HTTPStatus.UNPROCESSABLE_ENTITY):
        self.endpoint(connection, e)

  def base_test_importances_not_enough(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**self.experiment_meta)
    connection.experiments(e.id).observations().create(
      assignments=random_assignments(e), values=[{"value": 0}], no_optimize=True
    )
    with RaisesApiException(HTTPStatus.UNPROCESSABLE_ENTITY):
      self.endpoint(connection, e)

  def base_test_importances_not_on_development(self, development_connection, client_id):
    connection = development_connection
    e = self.create_experiment_and_observations(connection, client_id, self.experiment_meta)
    with RaisesApiException(HTTPStatus.UNPROCESSABLE_ENTITY):
      self.endpoint(connection, e)
