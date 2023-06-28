# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

import pytest

from zigopt.handlers.experiments.stopping_criteria import LOOKBACK_FACTOR, NUM_TOP_RESULTS_TO_CHECK

from integration.utils.make_values import make_values
from integration.utils.random_assignment import random_assignments
from integration.v1.test_base import V1Base


class TestExperimentStoppingCriteria(V1Base):
  @staticmethod
  def make_observation(experiment, values):
    values_list = make_values(experiment, values)
    return {"assignments": random_assignments(experiment), "no_optimize": True, "values": values_list}

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  def test_stopping_stagnation(self, connection):
    e = connection.create_any_experiment(observation_budget=499)
    dim = len(e.parameters)
    stagnation_check_length = LOOKBACK_FACTOR * dim + NUM_TOP_RESULTS_TO_CHECK

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

    for value in range(NUM_TOP_RESULTS_TO_CHECK):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [value]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert not stopping_criteria.should_stop

    for value in range(stagnation_check_length - NUM_TOP_RESULTS_TO_CHECK - 1):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [-1]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert not stopping_criteria.should_stop

    connection.experiments(e.id).observations().create(**self.make_observation(e, [-1]))
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert stopping_criteria.should_stop
    assert set(stopping_criteria.reasons) == {"possible_stagnation"}

    connection.experiments(e.id).observations().create(**self.make_observation(e, [NUM_TOP_RESULTS_TO_CHECK]))
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

    for _ in range(stagnation_check_length - 2):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [NUM_TOP_RESULTS_TO_CHECK]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert not stopping_criteria.should_stop

    for _ in range(NUM_TOP_RESULTS_TO_CHECK):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [NUM_TOP_RESULTS_TO_CHECK]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert stopping_criteria.should_stop
      assert set(stopping_criteria.reasons) == {"possible_stagnation"}

    connection.experiments(e.id).observations().delete()
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

  def test_stopping_stagnation_minimized(self, connection, config_broker):
    e = connection.create_any_experiment(metrics=[dict(name="metric", objective="minimize")])
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

    dim = len(e.parameters)
    stagnation_check_length = LOOKBACK_FACTOR * dim + NUM_TOP_RESULTS_TO_CHECK

    for i in range(stagnation_check_length):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [-i]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert not stopping_criteria.should_stop

    for i in range(stagnation_check_length):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [i]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()

    assert stopping_criteria.should_stop
    assert set(stopping_criteria.reasons) == {"possible_stagnation"}

  def test_stopping_budget(self, connection):
    e = connection.create_any_experiment(observation_budget=5)
    dim = len(e.parameters)

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

    for k in range(e.observation_budget):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [k]))
      stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
      assert not stopping_criteria.should_stop

    connection.experiments(e.id).observations().create(**self.make_observation(e, [0]))
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert stopping_criteria.should_stop
    assert set(stopping_criteria.reasons) == {"observation_budget_reached"}

    for _ in range(LOOKBACK_FACTOR * dim - 1):
      connection.experiments(e.id).observations().create(**self.make_observation(e, [0]))

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert stopping_criteria.should_stop
    assert set(stopping_criteria.reasons) == {"possible_stagnation", "observation_budget_reached"}

    connection.experiments(e.id).observations().delete()
    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

  def test_multimetric_stopping_criteria(self, connection, client_id):
    meta = {
      "name": "test",
      "parameters": [{"name": "x", "type": "double", "bounds": {"min": 0, "max": 10}}],
      "metrics": [{"name": "f1"}, {"name": "f2"}],
      "observation_budget": 20,
    }
    e = connection.clients(client_id).experiments().create(**meta)

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert not stopping_criteria.should_stop

    observations: list[dict[str, Any]] = []
    for k in range(e.observation_budget + 1):
      x = 10 * (e.observation_budget - k) / e.observation_budget
      f1 = 1 - (x - 5) ** 2
      f2 = 1 - (x - 9) ** 2
      observations.append(
        {
          "assignments": {"x": x},
          "values": [{"name": "f1", "value": f1}, {"name": "f2", "value": f2}],
        }
      )
    self.batch_upload_observations(e, observations)

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert stopping_criteria.should_stop and "observation_budget_reached" in stopping_criteria.reasons

    # This is only going to work because I know how the internals of stagnation work
    observations = []
    x = 1.23456
    for _ in range(50):
      f1 = 1 - (x - 5) ** 2
      f2 = 1 - (x - 9) ** 2
      observations.append(
        {
          "assignments": {"x": x},
          "values": [{"name": "f1", "value": f1}, {"name": "f2", "value": f2}],
        }
      )
    self.batch_upload_observations(e, observations)

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert {"possible_stagnation", "observation_budget_reached"} == set(stopping_criteria.reasons)

    # Make sure that failures don't fuck this up
    observations = [{"assignments": {"x": 2.3456}, "failed": True} for _ in range(50)]
    self.batch_upload_observations(e, observations)

    stopping_criteria = connection.experiments(e.id).stopping_criteria().fetch()
    assert {"possible_stagnation", "observation_budget_reached"} == set(stopping_criteria.reasons)
