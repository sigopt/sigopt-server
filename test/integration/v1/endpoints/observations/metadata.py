# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus
from typing import Any

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestObservationMetadata(V1Base):
  def test_create_with_metadata(self, connection):
    with connection.create_any_experiment() as experiment:
      # create with suggestion id
      metadata = {"foo": "bar"}
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(values=[{"value": 5.1}], suggestion=suggestion.id, metadata=metadata)
      )
      assert observation.metadata.to_json() == metadata
      # create with assignments
      metadata = {"biz": "baz"}
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(values=[{"value": 7.2}], assignments=suggestion.assignments, metadata=metadata)
      )
      assert observation.metadata.to_json() == metadata
      # metadata preserved on detail
      observation = connection.experiments(experiment.id).observations(observation.id).fetch()
      assert observation.metadata.to_json() == metadata

  def test_create_with_invalid_metadata(self, connection):
    metadata: Any

    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      metadata = ["foo", "bar"]
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          values=[{"value": 4.3}],
          suggestion=suggestion.id,
          metadata=metadata,
        )

      metadata = {"baz": ["foo", "bar"]}
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          values=[{"value": 4.3}],
          suggestion=suggestion.id,
          metadata=metadata,
        )

  def test_create_with_long_metadata(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      metadata = {x: x for x in range(500)}
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          values=[{"value": 4.3}],
          suggestion=suggestion.id,
          metadata=metadata,
        )

  def test_update_metadata(self, connection):
    metadata: Any

    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          values=[{"value": 4.7}],
          suggestion=suggestion.id,
          no_optimize=True,
        )
      )
      # set metadata
      metadata = {"foo": "bar"}
      observation = (
        connection.experiments(experiment.id)
        .observations(observation.id)
        .update(
          metadata=metadata,
          no_optimize=True,
        )
      )
      assert observation.metadata.to_json() == metadata
      # change metadata
      metadata = {"biz": "baz"}
      observation = (
        connection.experiments(experiment.id)
        .observations(observation.id)
        .update(
          metadata=metadata,
          no_optimize=True,
        )
      )
      assert observation.metadata.to_json() == metadata
      # update with no effect
      observation = connection.experiments(experiment.id).observations(observation.id).update(no_optimize=True)
      assert observation.metadata.to_json() == metadata
      # unset metadata
      metadata = None
      observation = (
        connection.experiments(experiment.id)
        .observations(observation.id)
        .update(
          metadata=metadata,
          no_optimize=True,
        )
      )
      assert observation.metadata is None
