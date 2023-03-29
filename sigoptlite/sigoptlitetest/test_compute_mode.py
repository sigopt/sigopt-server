# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import numpy.random
import pytest
from sigopt import Connection

from libsigopt.compute.views.rest.gp_next_points_categorical import GpNextPointsCategorical
from libsigopt.compute.views.rest.search_next_points import SearchNextPoints
from libsigopt.compute.views.rest.spe_next_points import SPENextPoints
from libsigopt.compute.views.rest.spe_search_next_points import SPESearchNextPoints
from sigoptlite.driver import LocalDriver
from sigoptlite.models import FIXED_EXPERIMENT_ID
from sigoptlitetest.constants import PARAMETER_DOUBLE, PARAMETER_INT


class TestComputeMode(object):
  @staticmethod
  def create_toy_experiment(conn, search=False):
    if search:
      metrics = [dict(name="y1", objective="maximize", strategy="constraint", threshold=0.5)]
    else:
      metrics = [dict(name="y1", objective="maximize", strategy="optimize")]
    experiment_meta = dict(parameters=[PARAMETER_DOUBLE, PARAMETER_INT], metrics=metrics, observation_budget=100)
    experiment = conn.experiments().create(**experiment_meta)
    return experiment

  @staticmethod
  def move_past_initialization(conn):
    eid = FIXED_EXPERIMENT_ID
    experiment = conn.experiments(eid).fetch()
    num_random = 2 * len(experiment.parameters) + 1
    for i in range(num_random):
      conn.experiments(experiment.id).observations().create(
        assignments=dict(d1=numpy.random.uniform(low=0, high=10), i1=numpy.random.randint(low=10, high=20)),
        values=[dict(name="y1", value=i)],
      )

  def test_wrong_flag(self):
    with pytest.raises(ValueError):
      # pylint: disable=unexpected-keyword-arg
      Connection(driver=LocalDriver, compute_mode="not_valid")

  @mock.patch.object(GpNextPointsCategorical, "view")
  def test_correct_routing_gp_optimization(self, mock_view):
    fake_point = [1.2345, 11]
    mock_view.return_value = {"points_to_sample": [fake_point]}
    # pylint: disable=unexpected-keyword-arg
    conn = Connection(driver=LocalDriver)
    e = self.create_toy_experiment(conn)
    self.move_past_initialization(conn)

    suggestion = conn.experiments(e.id).suggestions().create()
    assert list(suggestion.assignments.values()) == fake_point

  @mock.patch.object(SPENextPoints, "view")
  def test_correct_routing_spe_optimization(self, mock_view):
    fake_point = [2.3456, 12]
    mock_view.return_value = {"points_to_sample": [fake_point]}
    # pylint: disable=unexpected-keyword-arg
    conn = Connection(driver=LocalDriver, compute_mode="kde_only")
    e = self.create_toy_experiment(conn)
    self.move_past_initialization(conn)

    suggestion = conn.experiments(e.id).suggestions().create()
    assert list(suggestion.assignments.values()) == fake_point

  @mock.patch.object(SearchNextPoints, "view")
  def test_correct_routing_gp_search(self, mock_view):
    fake_point = [3.4567, 13]
    mock_view.return_value = {"points_to_sample": [fake_point]}
    # pylint: disable=unexpected-keyword-arg
    conn = Connection(driver=LocalDriver)
    e = self.create_toy_experiment(conn, search=True)
    self.move_past_initialization(conn)

    suggestion = conn.experiments(e.id).suggestions().create()
    assert list(suggestion.assignments.values()) == fake_point

  @mock.patch.object(SPESearchNextPoints, "view")
  def test_correct_routing_spe_search(self, mock_view):
    fake_point = [4.5678, 14]
    mock_view.return_value = {"points_to_sample": [fake_point]}
    # pylint: disable=unexpected-keyword-arg
    conn = Connection(driver=LocalDriver, compute_mode="kde_only")
    e = self.create_toy_experiment(conn, search=True)
    self.move_past_initialization(conn)

    suggestion = conn.experiments(e.id).suggestions().create()
    assert list(suggestion.assignments.values()) == fake_point
