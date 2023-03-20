# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestValueFailed(V1Base):
  @pytest.fixture
  def experiment(self, connection):
    with connection.create_any_experiment() as experiment:
      yield experiment

  @pytest.fixture
  def suggestion(self, connection, experiment):
    return connection.experiments(experiment.id).suggestions().create()

  @pytest.fixture(params=[{"values": [{"value": 1}]}, {"failed": True}])
  def observation(self, request, connection, suggestion, experiment):
    return connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, **request.param)

  def test_update_failed_true_with_none_values(self, connection, experiment, observation):
    updated = connection.experiments(experiment.id).observations(observation.id).update(failed=True, values=None)
    assert updated.failed is True
    assert not updated.values

  def test_update_value_with_failed(self, connection, experiment, observation):
    updated = (
      connection.experiments(experiment.id).observations(observation.id).update(values=[{"value": 3}], failed=False)
    )
    assert updated.failed is False
    assert updated.values[0].value == 3

  def test_update_values_with_failed(self, connection, experiment, observation):
    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        values=[
          {
            "name": "",
            "value": 3,
            "value_stddev": 1,
          }
        ],
        failed=False,
      )
    )
    assert updated.failed is False
    assert updated.values[0].value == 3
    assert updated.values[0].value_stddev == 1

  def test_update_invalid_values(self, connection, experiment, observation):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          {
            "name": "",
            "values": None,
          }
        ],
        failed=False,
      )

  def test_invalid_updates(self, connection, experiment, observation):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(failed=False, values=[{"value": None}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(failed=True, values=[{"value": 1}])

  def test_update_just_failed(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      failed_observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          failed=True,
          no_optimize=True,
        )
      )
      updated = (
        connection.experiments(experiment.id)
        .observations(failed_observation.id)
        .update(
          failed=True,
          no_optimize=True,
        )
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(failed_observation.id).update(
          failed=False,
          no_optimize=True,
        )
      assert updated.failed is True
      assert not updated.values
      value_observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          values=[{"value": 1}],
          no_optimize=True,
        )
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(value_observation.id).update(
          failed=True,
          no_optimize=True,
        )
      updated = (
        connection.experiments(experiment.id)
        .observations(value_observation.id)
        .update(
          failed=False,
          no_optimize=True,
        )
      )
      assert updated.failed is False
      assert updated.values[0].value == 1

  def test_update_just_value(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      failed_observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          failed=True,
          no_optimize=True,
        )
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(failed_observation.id).update(
          values=[{"value": 3}],
          no_optimize=True,
        )
      updated = (
        connection.experiments(experiment.id)
        .observations(failed_observation.id)
        .update(
          values=None,
          no_optimize=True,
        )
      )
      assert updated.failed is True
      assert not updated.values

      value_observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          suggestion=suggestion.id,
          values=[{"value": 1}],
          no_optimize=True,
        )
      )
      updated = (
        connection.experiments(experiment.id)
        .observations(value_observation.id)
        .update(
          values=[{"value": 3}],
          no_optimize=True,
        )
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(value_observation.id).update(
          no_optimize=True,
          values=[{"value": None}],
        )
