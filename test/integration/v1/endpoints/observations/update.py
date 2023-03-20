# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.endpoints.observations.stored_metrics_mixin import StoredMetricsMixin
from integration.v1.test_base import V1Base


class TestUpdateObservations(V1Base):
  @pytest.fixture
  def experiment(self, connection):
    with connection.create_experiment(self.offline_experiment_meta) as experiment:
      yield experiment

  @pytest.fixture
  def multimetric_experiment(self, connection):
    with connection.create_experiment(self.offline_multimetric_experiment_meta) as multimetric_experiment:
      yield multimetric_experiment

  @pytest.fixture
  def suggestion(self, connection, experiment):
    return connection.experiments(experiment.id).suggestions().create()

  @pytest.fixture
  def observation_from_suggestion(self, connection, suggestion, experiment):
    return (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[
          dict(
            value=1,
            value_stddev=0.1,
          )
        ],
        suggestion=suggestion.id,
      )
    )

  @pytest.fixture
  def observation_from_assignments(self, connection, suggestion, experiment):
    return (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[
          dict(
            value=1,
            value_stddev=0.1,
          )
        ],
        assignments=suggestion.assignments,
      )
    )

  @pytest.fixture(params=["suggestion", "assignments"])
  def observation(self, request, observation_from_suggestion, observation_from_assignments):
    if request.param == "suggestion":
      return observation_from_suggestion
    elif request.param == "assignments":
      return observation_from_assignments
    return None

  @pytest.mark.parametrize(
    "kwargs",
    [
      {"values": [{"name": None, "value": 2.6}]},
    ],
  )
  def test_update_observation_value(self, connection, experiment, observation, kwargs):
    def check_values(obj):
      assert obj.value == 2.6
      assert obj.value_stddev == 0.1

    updated_observation = connection.experiments(experiment.id).observations(observation.id).update(**kwargs)
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])
    updated_observation = connection.experiments(experiment.id).observations(observation.id).fetch()
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])

  @pytest.mark.parametrize(
    "kwargs",
    [
      {"values": [{"name": None, "value": 1, "value_stddev": 0.5}]},
    ],
  )
  def test_update_observation_value_stddev(self, connection, experiment, observation, kwargs):
    def check_values(obj):
      assert obj.value == 1.0
      assert obj.value_stddev == 0.5

    updated_observation = connection.experiments(experiment.id).observations(observation.id).update(**kwargs)
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])
    updated_observation = connection.experiments(experiment.id).observations(observation.id).fetch()
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])

  @pytest.mark.parametrize(
    "kwargs",
    [
      {"values": [{"name": None, "value": 1, "value_stddev": None}]},
    ],
  )
  def test_erase_value_stddev(self, connection, experiment, observation, kwargs):
    def check_values(obj):
      assert obj.value == 1.0
      assert obj.value_stddev is None

    updated_observation = connection.experiments(experiment.id).observations(observation.id).update(**kwargs)
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])
    updated_observation = connection.experiments(experiment.id).observations(observation.id).fetch()
    assert updated_observation.id == observation.id
    assert updated_observation.suggestion == observation.suggestion
    check_values(updated_observation.values[0])

  def test_update_suggestion(self, connection, experiment, observation, suggestion):
    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        suggestion=suggestion.id,
        assignments=None,
      )
    )
    assert updated.suggestion == suggestion.id
    assert updated.assignments == suggestion.assignments

  def test_nullify_suggestion_with_assignments(self, connection, experiment, observation, suggestion):
    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        suggestion=None,
        assignments=suggestion.assignments,
      )
    )
    assert updated.suggestion is None
    assert updated.assignments == suggestion.assignments

  def test_invalid_updates(self, connection, experiment, observation, suggestion):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(assignments=None, suggestion=None)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        assignments=suggestion.assignments,
        suggestion=suggestion.id,
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(values=None)

  def test_update_observation_from_suggestion(self, connection, experiment, observation_from_suggestion):
    observation = observation_from_suggestion
    suggestion = connection.experiments(experiment.id).suggestions().create()

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        suggestion=None,
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(assignments=suggestion.assignments)

    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        assignments=None,
      )
    )
    assert updated.suggestion == observation.suggestion
    assert updated.assignments == observation.assignments

    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        suggestion=suggestion.id,
      )
    )
    assert updated.suggestion == suggestion.id
    assert updated.assignments == suggestion.assignments

  def test_update_observation_from_assignments(self, connection, experiment, observation_from_assignments):
    observation = observation_from_assignments
    suggestion = connection.experiments(experiment.id).suggestions().create()

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        assignments=None,
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        suggestion=suggestion.id,
      )

    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        suggestion=None,
      )
    )
    assert updated.suggestion is None
    assert updated.assignments == observation.assignments

    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        assignments=suggestion.assignments,
      )
    )
    assert updated.suggestion is None
    assert updated.assignments == suggestion.assignments

  def test_update_failed_experiment(self, connection, experiment, observation):
    updated = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        values=None,
        failed=True,
      )
    )
    assert updated.failed is True

  def test_observation_update_metadata(self, connection, experiment, observation):
    obs = (
      connection.experiments(experiment.id).observations(observation.id).update(metadata=dict(changed_metadata="True"))
    )
    assert obs.metadata["changed_metadata"] == "True"

  def test_observation_update_multimetric_experiment(self, connection, multimetric_experiment):
    suggestion = connection.experiments(multimetric_experiment.id).suggestions().create()
    observation = (
      connection.experiments(multimetric_experiment.id)
      .observations()
      .create(
        values=[dict(name="metric1", value=0), dict(name="metric2", value=1)],
        suggestion=suggestion.id,
      )
    )
    connection.experiments(multimetric_experiment.id).observations(observation.id).update()

  @pytest.mark.parametrize(
    "invalid_update",
    [
      {"values": [dict(name="wrong_metric_name", value=1)], "failed": False},
      {"values": [dict(name="metric", value=1), dict(name="metric_that_doesnt_exist", value=1)], "failed": False},
    ],
  )
  def test_update_observation_from_failed(self, connection, invalid_update):
    with connection.create_experiment(self.offline_named_metric_experiment_meta) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          failed=True,
          suggestion=suggestion.id,
        )
      )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(**invalid_update)

  @pytest.mark.parametrize(
    "invalid_update",
    [
      {"values": [dict(name="metric1", value=1)]},
      {"values": [dict(name="metric1", value=1), dict(name="invalid_name", value=1)]},
    ],
  )
  def test_update_observation_invalid_multimetric(self, connection, multimetric_experiment, invalid_update):
    suggestion = connection.experiments(multimetric_experiment.id).suggestions().create()
    observation = (
      connection.experiments(multimetric_experiment.id)
      .observations()
      .create(
        values=[dict(name="metric1", value=1), dict(name="metric2", value=2)],
        suggestion=suggestion.id,
      )
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(multimetric_experiment.id).observations(observation.id).update(**invalid_update)

  def test_invalid_suggestion(self, connection, experiment, suggestion, observation_from_suggestion):
    with connection.create_experiment(self.offline_experiment_meta) as other_experiment:
      s = connection.experiments(other_experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(observation_from_suggestion.id).update(suggestion=s.id)
      connection.experiments(experiment.id).observations(observation_from_suggestion.id).update(
        suggestion=suggestion.id,
      )


class TestUpdateObservationsWithStoredMetrics(V1Base, StoredMetricsMixin):
  @pytest.fixture
  def observation(self, connection, experiment, suggestion, optimized_metric_name, stored_metric_name):
    return (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        values=[
          dict(name=optimized_metric_name, value=321),
          dict(name=stored_metric_name, value=654),
        ],
      )
    )

  def test_update_obseravtion_with_stored_metrics(
    self,
    connection,
    experiment,
    observation,
    optimized_metric_name,
    stored_metric_name,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(values=[{"value": 123}])

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          dict(name=optimized_metric_name, value=123),
        ],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          dict(name=stored_metric_name, value=456),
        ],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=None),
        ],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=456),
        ],
        failed=True,
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations(observation.id).update(
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=456),
          dict(name="some-fake-metric", value=789),
        ],
      )

    observation = (
      connection.experiments(experiment.id)
      .observations(observation.id)
      .update(
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=456),
        ],
      )
    )
    assert observation.values[0].name == optimized_metric_name
    assert observation.values[0].value == 123
    assert observation.values[1].name == stored_metric_name
    assert observation.values[1].value == 456
    assert observation.failed is False
