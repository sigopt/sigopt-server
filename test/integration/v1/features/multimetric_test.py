# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.utils.make_values import make_values
from integration.utils.random_assignment import random_assignments
from integration.v1.constants import (
  EXPERIMENT_META_MULTIMETRIC,
  EXPERIMENT_META_MULTIMETRIC_MINIMIZED,
  EXPERIMENT_META_MULTIMETRIC_THRESHOLD,
)
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase


class MultimetricExperimentFeaturesTestBase(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self, connection, request):
    meta_dict = getattr(request, "param", EXPERIMENT_META_MULTIMETRIC)
    meta = copy.deepcopy(meta_dict)
    return meta


class TestExperimentsMultimetric(MultimetricExperimentFeaturesTestBase):
  @pytest.mark.parametrize("observation_budget", [None, -1000])
  def test_invalid_budget(self, connection, client_id, meta, observation_budget):
    meta.update(observation_budget=observation_budget)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_metrics_list_too_many_metrics(self, connection, client_id, meta):
    meta["metrics"].append({"name": "too_many_metrics"})
    assert len(meta["metrics"]) > 2
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_update_budget(self, connection, meta):
    # Cannot change the budget for a multimetric experiment
    e = connection.create_any_experiment(**meta)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(observation_budget=meta["observation_budget"] + 1)

  # NOTE: May need to modify or supplement test to account for alphabetical return of metrics
  @pytest.mark.parametrize(
    "meta, best_obs_returned, metric_values",
    [
      (
        EXPERIMENT_META_MULTIMETRIC,
        [[4, 5], [9, 3], [2, 8]],
        [[4, 5], [0, 1], [9, 3], [3, 2], [1, 3], [2, 8]],
      ),
      (
        EXPERIMENT_META_MULTIMETRIC_MINIMIZED,
        [[-4, -5], [-9, -3], [-2, -8]],
        [[-4, -5], [-0, -1], [-9, -3], [-3, -2], [-1, -3], [-2, -8]],
      ),
      (
        EXPERIMENT_META_MULTIMETRIC_THRESHOLD,
        [[4, 5], [2, 8]],
        [[4, 5], [0, 1], [9, 3], [3, 2], [1, 3], [2, 8]],
      ),
    ],
    ids=[
      "EXPERIMENT_META_MULTIMETRIC",
      "EXPERIMENT_META_MULTIMETRIC_MINIMIZED",
      "EXPERIMENT_META_MULTIMETRIC_THRESHOLD",
    ],
    indirect=["meta"],
  )
  def test_best_assignments(self, connection, client_id, meta, best_obs_returned, metric_values, config_broker):
    e = connection.clients(client_id).experiments().create(**meta)
    for vals in metric_values:
      assignments = random_assignments(e)
      connection.experiments(e.id).observations().create(
        assignments=assignments,
        values=make_values(e, vals),
        no_optimize=True,
      )
    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == len(best_obs_returned)
    for data in a.data:
      assert data.value is None
      assert data.value_stddev is None
      assert [v.value for v in data.values] in best_obs_returned
