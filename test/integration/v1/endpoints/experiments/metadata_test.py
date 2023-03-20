# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentMetadata(ExperimentsTestBase):
  def test_create_with_metadata(self, connection, client_id):
    metadata = dict(foo="bar")
    e = connection.create_any_experiment(
      client_id=client_id,
      metadata=metadata,
    )
    assert e.metadata.to_json() == metadata
    e = connection.experiments(e.id).fetch()
    assert e.metadata.to_json() == metadata

  def test_create_with_null_metadata(self, connection, client_id):
    e = connection.create_any_experiment(
      client_id=client_id,
      metadata=dict(foo="bar", nullkey=None),
    )
    assert e.metadata.to_json() == dict(foo="bar")

  @pytest.mark.parametrize(
    "metadata",
    [
      ["foo", "bar"],
      dict(bar=["foo", "bar"]),
    ],
  )
  def test_create_with_invalid_metadata(self, connection, client_id, metadata):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        metadata=metadata,
      )

  def test_create_with_long_metadata(self, connection, client_id):
    metadata = {x: x for x in range(500)}
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        client_id=client_id,
        metadata=metadata,
      )

  def test_update_metadata(self, connection, client_id):
    with connection.create_any_experiment(client_id=client_id) as e:
      # set metadata
      metadata = {"foo": "bar"}
      e = connection.experiments(e.id).update(metadata=metadata)
      assert e.metadata.to_json() == metadata
      # change metadata
      metadata = {"biz": "baz"}
      e = connection.experiments(e.id).update(metadata=metadata)
      assert e.metadata.to_json() == metadata
      # update with no effect
      e = connection.experiments(e.id).update()
      assert e.metadata.to_json() == metadata
      # unset metadata
      metadata = None
      e = connection.experiments(e.id).update(metadata=metadata)
      assert e.metadata is None
