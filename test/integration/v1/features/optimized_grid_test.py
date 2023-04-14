# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus
from typing import Any

import pytest

from integration.base import RaisesApiException
from integration.v1.constants import (
  DEFAULT_EXPERIMENT_META,
  EXPERIMENT_META_WITH_CONSTRAINTS,
  AnyParameterMetaType,
  GriddedDoubleParameterMetaType,
  GriddedIntegerParameterMetaType,
)
from integration.v1.test_base import V1Base


GOOD_GRID_PARAMS: list[GriddedDoubleParameterMetaType | GriddedIntegerParameterMetaType] = [
  dict(name="grid_param", type="int", grid=[1, 2, 3]),
  dict(name="grid_param", type="double", grid=[0.1, 2, 0.3]),
  dict(name="grid_param", type="int", grid=[3, 2, 1]),
  dict(name="grid_param", type="double", grid=[7, 8, 9, -10.5]),
  dict(name="grid_param", type="int", grid=[-1, 5, -99]),
]

BAD_GRID_PARAMS: list[dict[str, Any]] = [
  dict(name="grid_param", type="int", grid=None),
  dict(name="grid_param", type="double", grid="a"),
  dict(name="grid_param", type="int", grid=1),
  dict(name="grid_param", type="double", grid=["a", 8, 9, 10]),
  dict(name="grid_param", type="int", grid=[None, 8, 9, 10]),
  dict(name="grid_param", type="double", grid=[33]),
  dict(name="grid_param", type="int", grid=[]),
  dict(name="grid_param", type="int", grid=[1, 33, 33]),
]

BASIC_GRID_PARAM: GriddedIntegerParameterMetaType = dict(name="grid_param", type="int", grid=[1, 2, 3])


# Note: API sorts grid values so we can't compare them directly
def compare_and_validate_grid_params(param, api_param):
  assert api_param.name == param["name"]
  assert api_param.type == param["type"]
  assert api_param.grid == sorted(param["grid"])
  assert api_param.bounds.min == min(param["grid"])
  assert api_param.bounds.max == max(param["grid"])


class TestOptimizedGrid(V1Base):
  @pytest.mark.parametrize("grid_param", GOOD_GRID_PARAMS)
  def test_valid_grid(self, connection, grid_param):
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)

    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)
    api_grid_param = [param for param in e.parameters if param.grid][0]
    compare_and_validate_grid_params(grid_param, api_grid_param)

  @pytest.mark.parametrize("grid_param", BAD_GRID_PARAMS)
  def test_invalid_grid(self, connection, grid_param):
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).experiments().create(**experiment_meta)

  def test_wrong_param_type(self, connection):
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    grid_param = GriddedIntegerParameterMetaType(
      name="grid_param",
      type="int",
      grid=[0, 1, 2, 3.5],  # type: ignore
    )
    experiment_meta["parameters"].append(grid_param)

    with RaisesApiException(HTTPStatus.BAD_REQUEST) as error:
      connection.clients(connection.client_id).experiments().create(**experiment_meta)
    assert "Invalid type" in error.value.message

  @pytest.mark.parametrize("grid_param", GOOD_GRID_PARAMS)
  def test_update_existing_grid_with_good(self, connection, grid_param):
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(dict(name=grid_param["name"], type=grid_param["type"], grid=[1, 2, 3]))
    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)

    updated_experiment = connection.experiments(e.id).update(parameters=[grid_param])

    updated_grid_param = [param for param in updated_experiment.parameters if param.grid][0]
    compare_and_validate_grid_params(grid_param, updated_grid_param)

  @pytest.mark.parametrize("bad_param", [param for param in BAD_GRID_PARAMS if param["grid"] is not None])
  def test_update_existing_grid_with_bad(self, connection, bad_param):
    grid_param = dict(name=bad_param["name"], type=bad_param["type"], grid=[1, 2, 3])  # type: ignore
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)  # type: ignore
    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)

    grid_param["grid"] = bad_param["grid"]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[grid_param])

  def test_multiple_grid_params(self, connection):
    grid_param1 = GriddedIntegerParameterMetaType(
      name="grid_1",
      type="int",
      grid=[0, 1, 2, 3],
    )
    grid_param2 = GriddedDoubleParameterMetaType(
      name="grid_2",
      type="double",
      grid=[0, 1, 4.1, 3, 4],
    )

    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].extend([grid_param1, grid_param2])

    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)
    grid_param1_api = [param for param in e.parameters if param.name == grid_param1["name"]][0]
    compare_and_validate_grid_params(grid_param1, grid_param1_api)
    grid_param2_api = [param for param in e.parameters if param.name == grid_param2["name"]][0]
    compare_and_validate_grid_params(grid_param2, grid_param2_api)

  def test_constraints_not_allowed_for_grid(self, connection):
    experiment_meta = copy.deepcopy(EXPERIMENT_META_WITH_CONSTRAINTS)
    connection.clients(connection.client_id).experiments().create(**experiment_meta)

    grid_param = GriddedDoubleParameterMetaType(
      name="grid_param",
      type="double",
      grid=[0.1, 0.2, 0.3, 0.4, 5, 10],
    )
    experiment_meta["parameters"].append(grid_param)
    connection.clients(connection.client_id).experiments().create(**experiment_meta)

    linear_constraint_with_grid = [
      dict(
        type="less_than",
        threshold=1,
        terms=[
          dict(name="grid_param", weight=1),
          dict(name="b", weight=1),
        ],
      )
    ]
    experiment_meta["linear_constraints"] = linear_constraint_with_grid  # type: ignore

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).experiments().create(**experiment_meta)

  def test_grid_param_works_with_log(self, connection):
    grid_param: GriddedDoubleParameterMetaType = dict(
      name="grid_param",
      type="double",
      grid=[0.01, 0.1, 10, 1000],
      transformation="log",
    )

    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)

    connection.clients(connection.client_id).experiments().create(**experiment_meta)

    grid_param_bad: GriddedDoubleParameterMetaType = dict(
      name="grid_param",
      type="double",
      grid=[0.01, 0.1, 10, 1000, 0],
      transformation="log",
    )

    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param_bad)

    with RaisesApiException(HTTPStatus.BAD_REQUEST) as error:
      connection.clients(connection.client_id).experiments().create(**experiment_meta)
    assert "log-transformation" in error.value.message

  def test_prior_beliefs_errors(self, connection):
    grid_param: AnyParameterMetaType = GriddedDoubleParameterMetaType(
      name="grid_param",
      type="double",
      grid=[0.01, 0.1, 10, 1000],
      prior=dict(
        name="normal",
        mean=0,
        scale=1,
      ),
    )

    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).experiments().create(**experiment_meta)

    grid_param = copy.deepcopy(BASIC_GRID_PARAM)
    double_grid_param = GriddedDoubleParameterMetaType(name="grid_param2", type="double", grid=[0.1, -2, 0.3])
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)
    experiment_meta["parameters"].append(double_grid_param)
    observation_budget = 30
    experiment_meta["observation_budget"] = observation_budget
    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)

    for i in range(observation_budget):
      s = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": i}])
      assert s.assignments["grid_param"] in BASIC_GRID_PARAM["grid"]

  def test_manual_observation(self, connection):
    grid_param = copy.deepcopy(BASIC_GRID_PARAM)
    experiment_meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    experiment_meta["parameters"].append(grid_param)
    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)

    max_grid_value = max(grid_param["grid"])

    assignments = dict(a=1, b=-2, c="d", grid_param=max_grid_value)

    connection.experiments(e.id).observations().create(assignments=assignments, values=[{"value": 1}])

    assignments["grid_param"] = max_grid_value + 1

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).observations().create(assignments=assignments, value=1)
