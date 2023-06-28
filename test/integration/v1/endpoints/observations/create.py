# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import sys
from copy import deepcopy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_EXPERIMENT_META
from integration.v1.endpoints.observations.multi_metric import DEFAULT_EXPERIMENT_META_NO_METRIC
from integration.v1.test_base import V1Base


class TestCreateObservations(V1Base):
  @pytest.fixture
  def experiment(self, connection):
    return connection.create_experiment(self.offline_experiment_meta)

  @pytest.fixture
  def suggestion(self, connection, experiment):
    return connection.experiments(experiment.id).suggestions().create()

  @pytest.mark.parametrize(
    "value",
    [
      0.0,
      5.1,
      sys.float_info.max,
      sys.float_info.min,
      -sys.float_info.max,
      -sys.float_info.min,
    ],
  )
  def test_create_observation_with_suggestion(self, connection, experiment, suggestion, value):
    observation = (
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": value}])
    )
    assert observation.values[0].value == value
    assert observation.values[0].value_stddev is None
    assert observation.suggestion == suggestion.id
    assert observation.assignments == suggestion.assignments
    assert observation.created is not None
    assert observation.metadata is None
    assert observation.failed is False

  @pytest.mark.parametrize(
    "observation_meta",
    [
      dict(values=[{"value": 5.1}], suggestion=0),
      dict(values=[{"value": 5.1}], suggestion=None),
      dict(values=[{"value": 5.1}]),
    ],
  )
  def test_create_invalid_suggestion(self, connection, experiment, observation_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(**observation_meta)
    assert connection.experiments(experiment.id).observations().fetch().count == 0

  def test_create_observation_with_assignments(self, connection, experiment, suggestion):
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[{"value": 5.1}],
        assignments=suggestion.assignments,
      )
    )
    assert observation.values[0].value == 5.1
    assert observation.values[0].value_stddev is None
    assert observation.suggestion is None
    assert observation.assignments == suggestion.assignments
    assert observation.created is not None
    assert observation.metadata is None
    assert observation.failed is False

  @pytest.mark.parametrize(
    "observation_meta",
    [
      dict(values=[{"value": 5.1}], assignments=dict()),
      dict(values=[{"value": 5.1}], assignments=None),
      dict(values=[{"value": 5.1}], assignments=dict(x=0.0)),
      dict(values=[{"value": 5.1}], assignments=dict(y=0.0)),
      dict(values=[{"value": 5.1}], assignments=dict(x=0.0, y=0.0, fake=0.0)),
    ],
  )
  def test_create_observation_invalid_assignments(self, connection, experiment, observation_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(**observation_meta)

  def test_create_observation_with_suggestion_and_assignments(self, connection, experiment, suggestion):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        assignments=suggestion.assignments,
        values=[{"value": 2.6}],
      )

  @pytest.mark.parametrize(
    "observation_meta",
    [
      dict(),
      dict(values=[{"value": None}]),
    ],
  )
  def test_create_observation_invalid_value(self, connection, experiment, suggestion, observation_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, **observation_meta)

  def test_create_observation_unknown_keys(self, connection, experiment, suggestion):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"value": 2.6}],
        foo="bar",
      )

  def test_create_observation_nested_unknown_keys(self, connection, experiment, suggestion):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"value": 2.6, "foo": "bar"}],
      )

  def test_create_observation_with_failure_no_value(self, connection, experiment, suggestion):
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        failed=True,
      )
    )
    assert not observation.values
    assert observation.suggestion == suggestion.id
    assert observation.assignments == suggestion.assignments
    assert observation.created is not None
    assert observation.metadata is None
    assert observation.failed is True

  def test_create_observation_with_failure_with_value(self, connection, experiment, suggestion):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        values=[{"value": 123}],
        suggestion=suggestion.id,
        failed=True,
      )

  @pytest.mark.parametrize(
    "failed_params",
    [
      {},
      {"failed": False},
    ],
  )
  @pytest.mark.parametrize(
    "values_params",
    [
      {},
      {"values": None},
      {"values": []},
    ],
  )
  def test_create_observation_without_failure_or_values(
    self, connection, experiment, suggestion, failed_params, values_params
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        **failed_params,
        **values_params,
      )

  # TODO(RTL-127): Maybe a better error structure in the legacy (no metrics defined) case
  def test_create_observation_with_legacy_experiment(self, connection):
    pytest.skip()
    e_meta = deepcopy(DEFAULT_EXPERIMENT_META_NO_METRIC)
    assert "metrics" not in e_meta and "metric" not in e_meta
    experiment = connection.create_any_experiment(**e_meta)
    suggestion = connection.experiments(experiment.id).suggestions().create()
    observation1 = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[{"value": 4}],
        suggestion=suggestion.id,
      )
    )
    assert observation1.values[0].value == 4
    observation2 = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[{"name": None, "value": 4}],
        suggestion=suggestion.id,
      )
    )
    assert observation2.values[0].value == 4
    assert observation1.id != observation2.id
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.experiments(experiment.id).observations().create(
        values=[{"name": "I was never given a name", "value": 4}],
        suggestion=suggestion.id,
      )
    assert '"I was never given a name"' in str(e.value)

  def test_assignments_have_valid_log_transform_bounds(self, connection):
    meta = deepcopy(DEFAULT_EXPERIMENT_META)
    meta["parameters"] = [
      dict(name="x1", type="double", bounds=dict(min=1, max=100), transformation="log"),
    ]
    e = connection.create_any_experiment(**meta)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(
        assignments=dict(x1=-1),
        values=[{"value": 1.23}],
      )

    o = (
      connection.experiments(e.id)
      .observations()
      .create(
        assignments=dict(x1=0.5),
        values=[{"value": 1.23}],
      )
    )
    assert o is not None
