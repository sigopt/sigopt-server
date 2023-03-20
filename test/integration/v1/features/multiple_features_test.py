# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.constants import (
  EXPERIMENT_META_CONDITIONALS,
  EXPERIMENT_META_MULTIMETRIC,
  EXPERIMENT_META_MULTISOLUTION,
  EXPERIMENT_META_WITH_CONSTRAINTS,
)
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentMultipleFeatures(ExperimentsTestBase):
  @pytest.fixture
  def experiment_meta_multimetric(self):
    return copy.deepcopy(EXPERIMENT_META_MULTIMETRIC)

  @pytest.fixture
  def experiment_meta_multisolution(self):
    return copy.deepcopy(EXPERIMENT_META_MULTISOLUTION)

  @pytest.fixture
  def experiment_meta_conditionals(self):
    return copy.deepcopy(EXPERIMENT_META_CONDITIONALS)

  @pytest.fixture
  def experiment_meta_with_constraints(self):
    return copy.deepcopy(EXPERIMENT_META_WITH_CONSTRAINTS)

  def test_experiment_create_multimetric_with_multisolution(
    self,
    connection,
    client_id,
    experiment_meta_multimetric,
  ):
    experiment_meta_multimetric["num_solutions"] = 2
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**experiment_meta_multimetric)

  def test_experiment_multisolution_with_categoricals(
    self,
    connection,
    client_id,
    experiment_meta_multisolution,
  ):
    experiment_meta_multisolution["parameters"].append(
      {
        "name": "e",
        "type": "categorical",
        "categorical_values": [{"name": "d"}, {"name": "e"}],
      }
    )
    experiment = connection.clients(client_id).experiments().create(**experiment_meta_multisolution)
    assert experiment.id is not None
    assert experiment.type == "offline"

  def test_experiment_multisolution_with_constraints(
    self,
    connection,
    client_id,
    experiment_meta_with_constraints,
  ):
    experiment_meta_with_constraints["num_solutions"] = 2
    experiment = connection.clients(client_id).experiments().create(**experiment_meta_with_constraints)
    assert experiment.id is not None
    assert experiment.linear_constraints is not None
    assert experiment.num_solutions == 2

  def test_experiment_create_conditionals_with_multimetric(
    self,
    connection,
    client_id,
    experiment_meta_conditionals,
  ):
    experiment_meta_conditionals["metrics"].append({"name": "second_optimized_metric"})
    experiment = connection.clients(client_id).experiments().create(**experiment_meta_conditionals)
    assert experiment.conditionals is not None
    assert len(experiment.metrics) == 2
    assert set(m.name for m in experiment.metrics) == set(["second_optimized_metric", "metric"])

  def test_experiment_create_conditionals_with_metric_constraints(
    self,
    connection,
    client_id,
    experiment_meta_conditionals,
  ):
    experiment_meta_conditionals["metrics"].extend(
      [
        {"name": "constraint_metric", "strategy": "constraint", "objective": "minimize", "threshold": 0.1},
        {"name": "store_metric", "strategy": "store"},
      ]
    )
    experiment = connection.clients(client_id).experiments().create(**experiment_meta_conditionals)
    assert experiment.conditionals is not None
    assert len(experiment.metrics) == 3
    assert set(m.name for m in experiment.metrics) == set(["constraint_metric", "store_metric", "metric"])

  def test_experiment_create_conditionals_with_multisolution(
    self,
    connection,
    client_id,
    experiment_meta_conditionals,
  ):
    # Conditionals don't work with multisolution
    experiment_meta_conditionals["num_solutions"] = 2
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**experiment_meta_conditionals)

  def test_experiment_create_conditionals_with_constraints(
    self,
    connection,
    client_id,
    experiment_meta_conditionals,
  ):
    # Constraints cannot be defined on conditioned parameters
    experiment_meta_conditionals["parameters"].append({"name": "f", "type": "double", "bounds": {"min": 0, "max": 1}})
    experiment_meta_conditionals["linear_constraints"] = [
      {
        "type": "greater_than",
        "terms": [
          {"name": "b", "weight": 1},
          {"name": "f", "weight": 1},
        ],
        "threshold": 1,
      }
    ]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**experiment_meta_conditionals)

    # Constraints work on unconditioned double parameters
    experiment_meta_conditionals["parameters"].append({"name": "g", "type": "double", "bounds": {"min": 0, "max": 1}})
    experiment_meta_conditionals["linear_constraints"] = [
      {
        "type": "greater_than",
        "terms": [
          {"name": "f", "weight": 1},
          {"name": "g", "weight": 1},
        ],
        "threshold": 1,
      }
    ]
    experiment = connection.clients(client_id).experiments().create(**experiment_meta_conditionals)
    assert experiment.conditionals is not None
    assert experiment.linear_constraints is not None
