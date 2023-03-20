# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class GridExperimentsTestBase(V1Base):
  @pytest.fixture
  def grid_meta(self):
    return dict(
      type="grid",
      name="Grid Experiment",
      parameters=[
        dict(name="a", type="int", grid=[1, 50]),
        dict(name="b", type="double", grid=[-50.5, 0]),
        dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e"), dict(name="f")]),
      ],
    )

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def organization_id(self, connection):
    return connection.organization_id


class TestCreateGridExperiment(GridExperimentsTestBase):
  def test_admins_can_create_grid_experiments(self, connection, client_id, grid_meta):
    connection.clients(client_id).experiments().create(**grid_meta)

  def test_observation_budget_with_grid(self, connection, client_id, grid_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(
        observation_budget=1,
        **grid_meta,
      )

  def test_explicit_grid_values(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        type="grid",
        name="Grid Experiment",
        parameters=[
          dict(name="a", type="int", grid=[2, 5, 50]),
          dict(name="b", type="double", grid=[-2, -5, -50]),
          dict(
            name="c",
            type="categorical",
            categorical_values=[dict(name="d"), dict(name="e"), dict(name="f")],
          ),
        ],
      )
    )
    param_map = dict((p.name, p) for p in e.parameters)
    assert e.observation_budget == 3 * 3 * 3
    assert param_map["a"].to_json()["grid"] == [2, 5, 50]
    assert param_map["b"].to_json()["grid"] == [-50, -5, -2]
    assert param_map["c"].to_json()["grid"] == ["d", "e", "f"]
    assert param_map["a"].to_json()["bounds"]["max"] == 50
    assert param_map["a"].to_json()["bounds"]["min"] == 2
    assert param_map["b"].to_json()["bounds"]["max"] == -2
    assert param_map["b"].to_json()["bounds"]["min"] == -50

  @pytest.mark.parametrize(
    "bad_param",
    [
      dict(name="a", type="int", bounds=dict(min=1, max=50), grid=2),
      dict(name="b", type="double", bounds=dict(min=-50, max=0), grid=3),
      dict(
        name="c",
        type="categorical",
        categorical_values=[dict(name="d"), dict(name="e"), dict(name="f")],
        grid=1,
      ),
    ],
  )
  def test_explicit_grid_bounds_disallowed(self, connection, client_id, bad_param):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(
        type="grid",
        name="Grid Experiment",
        parameters=[bad_param],
      )

  @pytest.mark.parametrize(
    "bad_param",
    [
      dict(name="a", type="int", grid=[]),
      dict(name="a", type="int", grid=0),
      dict(name="a", type="int", grid=None),
      dict(name="a", type="int", bounds=dict(min=-1, max=10), grid=3),
    ],
  )
  def test_invalid_grid_values(self, connection, client_id, bad_param):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(
        type="grid",
        name="Grid Experiment",
        parameters=[bad_param],
      )

  def test_multimetric(self, connection, client_id, grid_meta):
    e = connection.clients(client_id).experiments().create(metrics=[dict(name="a"), dict(name="b")], **grid_meta)
    assert e.observation_budget is not None

  def test_multisolution(self, connection, client_id, grid_meta):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        type="grid",
        name="Grid Experiment",
        parameters=[dict(name="a", type="int", grid=[1, 2, 3])],
        num_solutions=2,
      )
    )
    assert e.observation_budget is not None

  def test_grid_log_space(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        type="grid",
        name="Grid Experiment",
        parameters=[
          dict(name="a", type="double", grid=[0.1, 1, 10], transformation="log"),
          dict(name="b", type="double", grid=[1, 10, 100], transformation="log"),
        ],
      )
    )
    param_map = dict((p.name, p) for p in e.parameters)
    assert param_map["a"].to_json()["grid"] == [0.1, 1, 10]
    assert param_map["b"].to_json()["grid"] == [1, 10, 100]


class TestUpdateGridExperiment(GridExperimentsTestBase):
  def test_admins_can_create_grid_experiments(self, connection, client_id, grid_meta):
    e = connection.clients(client_id).experiments().create(**grid_meta)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        parameters=[
          dict(name="a", type="int", bounds=dict(min=1, max=50)),
          dict(name="b", type="double", bounds=dict(min=-50, max=0)),
          dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e"), dict(name="f")]),
        ]
      )

    connection.experiments(e.id).update(name="Foobar")
    e = connection.experiments(e.id).fetch()
    assert e.name == "Foobar"


class TestGridExperimentSuggestions(GridExperimentsTestBase):
  def test_suggestions(self, connection, client_id, grid_meta):
    e = connection.clients(client_id).experiments().create(**grid_meta)
    for _ in range(2):
      suggestions = [connection.experiments(e.id).suggestions().create() for _ in range(12)]
      assert [s.assignments.to_json() for s in suggestions] == [
        dict(a=1, b=-50.5, c="d"),
        dict(a=50, b=-50.5, c="d"),
        dict(a=1, b=0.0, c="d"),
        dict(a=50, b=0.0, c="d"),
        dict(a=1, b=-50.5, c="e"),
        dict(a=50, b=-50.5, c="e"),
        dict(a=1, b=0.0, c="e"),
        dict(a=50, b=0.0, c="e"),
        dict(a=1, b=-50.5, c="f"),
        dict(a=50, b=-50.5, c="f"),
        dict(a=1, b=0.0, c="f"),
        dict(a=50, b=0.0, c="f"),
      ]
      for s in suggestions:
        connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 1}])

  def test_more_suggestions_than_grid(self, connection, client_id, grid_meta):
    e = connection.clients(client_id).experiments().create(**grid_meta)
    for _ in range(14):
      suggestion = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": 1}])
      assert suggestion.id is not None


class TestGridExperimentObservations(GridExperimentsTestBase):
  def test_observations(self, connection, client_id, grid_meta):
    e = connection.clients(client_id).experiments().create(**grid_meta)
    for _ in range(14):
      suggestion = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"value": 0}],
      )
