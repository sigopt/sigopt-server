# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

from zigopt.experiment.constant import MetricStrategyNames

from integration.utils.make_values import make_values
from integration.utils.random_assignment import random_assignments
from integration.v1.experiments_test_base import ExperimentsTestBase


class BestAssignmentsTestBase(ExperimentsTestBase):
  def fetch_best_assignments(self, connection, experiment_id):
    return connection.experiments(experiment_id).best_assignments().fetch()


class TestExperimentBestAssignments(BestAssignmentsTestBase):
  def test_best_assignments_no_observations(self, connection, client_id, any_meta):
    e = connection.clients(client_id).experiments().create(**any_meta)
    a = self.fetch_best_assignments(connection, e.id)
    assert a.count == 0
    assert a.data == []

  def test_best_assignments_data(self, connection, client_id, any_meta):
    # pylint: disable=too-many-locals
    wider_meta = deepcopy(any_meta)
    wider_meta["parallel_bandwidth"] = 20
    e = connection.clients(client_id).experiments().create(**wider_meta)
    observations = []
    for i in range(len(e.parameters) * 3):
      s = connection.experiments(e.id).suggestions().create()
      observations.append({"suggestion": s.id, "values": make_values(e, i)})
    self.batch_upload_observations(e, observations, no_optimize=True)

    is_search = all(m.strategy == MetricStrategyNames.CONSTRAINT for m in e.metrics)
    num_optimized_metrics = sum(1 for metric in e.metrics if metric.strategy == MetricStrategyNames.OPTIMIZE)
    get_pareto_frontier = num_optimized_metrics > 1
    a = self.fetch_best_assignments(connection, e.id)
    if e.num_solutions is not None:
      assert a.count == e.num_solutions
    elif is_search:
      satisfy_constraints_counter = 0
      for observation in observations:
        constraint_metric_1, constraint_metric_2 = observation["values"]
        if constraint_metric_1["value"] >= 2.1 and constraint_metric_2["value"] >= -5.2:
          satisfy_constraints_counter = satisfy_constraints_counter + 1
      assert a.count == satisfy_constraints_counter
    elif get_pareto_frontier:
      assert a.count >= 1
    else:
      assert a.count == 1

  def test_best_assignments_failed(self, connection, client_id, any_meta):
    e = connection.clients(client_id).experiments().create(**any_meta)
    for _ in range(3):
      s = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=s.id, failed=True, no_optimize=True)

    a = self.fetch_best_assignments(connection, e.id)
    assert a.count == 0
    assert a.data == []
    experiment = connection.experiments(e.id).fetch()
    assert experiment.progress.best_observation is None

  def test_best_assignments_delete_observations(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id)
    best = None
    observations = []
    for val in [1, 10, 2, 5, 2, 5, 4]:
      assignments = random_assignments(e)
      if val == 10:
        best = assignments
      observations.append({"assignments": assignments, "values": make_values(e, val)})
    self.batch_upload_observations(e, observations, no_optimize=True)
    a = self.fetch_best_assignments(connection, e.id)
    assert a.count == 1
    assert a.data[0].values[0].value == 10
    assert a.data[0].assignments.to_json() == best

    connection.experiments(e.id).observations().delete()
    a = self.fetch_best_assignments(connection, e.id)
    assert a.data == []

  def test_best_assignments_minimized(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id, metrics=[dict(name="metric", objective="minimize")])
    s = connection.experiments(e.id).suggestions().create()
    for val in [1, 2]:
      connection.experiments(e.id).observations().create(suggestion=s.id, values=make_values(e, val), no_optimize=True)
    best = self.fetch_best_assignments(connection, e.id)
    assert best.count == 1
    assert best.data[0].values[0].value == 1

  def test_ignores_stored_metrics(self, connection, client_id):
    metrics = [
      {"name": "a-stored-metric", "strategy": MetricStrategyNames.STORE},
      {"name": "optimized-metric"},
    ]
    e = connection.create_any_experiment(client_id=client_id, metrics=metrics)
    s = connection.experiments(e.id).suggestions().create()
    # stored metric alphabetically first
    for values in [[1, 5], [3, 0]]:
      connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=make_values(e, values),
        no_optimize=True,
      )

    best = self.fetch_best_assignments(connection, e.id)
    assert best.count == 1
    assert best.data[0].values[0].name == "a-stored-metric"
    assert best.data[0].values[0].value == 1
    assert best.data[0].values[1].value == 5

  def test_multiple_optimized_ignores_stored_metrics(
    self,
    connection,
    client_id,
  ):
    metrics = [
      {"name": "a-stored-metric", "strategy": MetricStrategyNames.STORE},
      {"name": "optimized-metric-1"},
      {"name": "optimized-metric-2"},
    ]
    e = connection.create_any_experiment(client_id=client_id, metrics=metrics, observation_budget=10)
    s = connection.experiments(e.id).suggestions().create()
    # stored metric alphabetically first
    for values in [[1, 5, 0], [3, 0, 4], [10, 0, 0]]:
      connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=make_values(e, values),
        no_optimize=True,
      )

    best = self.fetch_best_assignments(connection, e.id)
    assert best.count == 2
    assert best.data[0].values[0].name == "a-stored-metric"
    stored_values = sorted(o.values[0].value for o in best.data)
    assert stored_values == [1, 3]
