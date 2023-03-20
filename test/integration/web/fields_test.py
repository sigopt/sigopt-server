# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.web.test_base import WebBase


class TestFields(WebBase):
  @pytest.fixture
  def observations_connection(self, api_connection):
    experiment = api_connection.create_any_experiment(
      name="Fields Test Experiment",
      parameters=[
        dict(
          name="double_param",
          bounds=dict(
            min=0,
            max=1,
          ),
          type="double",
        ),
        dict(
          name="integer_param",
          bounds=dict(
            min=0,
            max=1,
          ),
          type="int",
        ),
      ],
    )
    observations_connection = api_connection.experiments(experiment.id).observations()
    observations_connection.create(
      assignments=dict(double_param=0, integer_param=0),
      values=[{"value": 0}],
      no_optimize=True,
    )
    observations_connection.create(
      assignments=dict(double_param=1, integer_param=1),
      values=[{"value": 1}],
      no_optimize=True,
    )
    observations_connection.create(
      assignments=dict(double_param=0, integer_param=1),
      failed=True,
      no_optimize=True,
    )
    return observations_connection

  def test_observation_list_value_failed_fields(self, observations_connection):
    partial_observations = observations_connection.fetch(fields="values,failed").data
    assert [observation.failed for observation in partial_observations] == [True, False, False]
    assert not partial_observations[0].values
    assert [observation.values[0].value for observation in partial_observations[1:]] == [1, 0.0]
    for observation in partial_observations:
      assert observation.assignments is None

  def test_observation_list_invalid_field(self, observations_connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      observations_connection.fetch(fields="invalid")
