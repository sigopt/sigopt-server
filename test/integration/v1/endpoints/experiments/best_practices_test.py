# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

from zigopt.common import *

from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentsBestPractices(ExperimentsTestBase):
  def test_best_practices_endpoint(self, connection, client_id, any_meta):
    e = connection.clients(client_id).experiments().create(**any_meta)
    best_practices = connection.experiments(e.id).best_practices().fetch()
    violations = best_practices.to_json()["violations"]
    assert not violations

  def test_best_practices_violations(self, connection, client_id):
    e = connection.create_any_experiment(
      client_id=client_id,
      observation_budget=1,
      parallel_bandwidth=1,
    )
    for _ in range(3):
      s = connection.experiments(e.id).suggestions().create()

    for _ in range(2):
      connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=[{"value": 0}],
      )

    best_practices = connection.experiments(e.id).best_practices().fetch()
    violations = best_practices.to_json()["violations"]
    assert len(violations) == 2
    assert find(violations, lambda v: "observation_budget" in v)
    assert find(violations, lambda v: "parallel_bandwidth" in v)

  def test_observation_budget_multitask_violation(self, connection, client_id):
    multitask_meta = copy.deepcopy(self.offline_multitask_experiment_meta)
    multitask_meta["observation_budget"] = 1
    e = connection.clients(client_id).experiments().create(**multitask_meta)

    for _ in range(11):
      s = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=[{"value": 1}],
      )

    best_practices = connection.experiments(e.id).best_practices().fetch()
    violations = best_practices.to_json()["violations"]
    assert find(violations, lambda v: "observation_budget" in v)

  def test_best_practices_violations_default_parallel_bandwidth(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id)
    assert e.parallel_bandwidth is None
    for _ in range(3):
      connection.experiments(e.id).suggestions().create()

    best_practices = connection.experiments(e.id).best_practices().fetch()
    violations = best_practices.to_json()["violations"]
    assert len(violations) == 1
    assert find(violations, lambda v: "parallel_bandwidth" in v)
