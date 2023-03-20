# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from integration.base import RaisesApiException
from integration.v1.endpoints.observations.stored_metrics_mixin import StoredMetricsMixin
from integration.v1.test_base import V1Base


class TestCreateObservationsWithStoredMetrics(V1Base, StoredMetricsMixin):
  def test_create_observation_with_stored_metrics(
    self, connection, experiment, suggestion, optimized_metric_name, stored_metric_name
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        value=123,
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name=optimized_metric_name, value=123)],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name=stored_metric_name, value=123)],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=None),
        ],
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[
          dict(name=optimized_metric_name, value=123),
          dict(name=stored_metric_name, value=456),
          dict(name="some-fake-metric", value=789),
        ],
      )

    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
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
