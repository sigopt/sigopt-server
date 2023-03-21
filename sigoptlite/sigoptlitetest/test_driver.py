# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import numpy
import pytest
from sigopt import Connection

from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.driver import LocalDriver
from sigoptlite.models import FIXED_EXPERIMENT_ID
from sigoptlitetest.base_test import UnitTestsBase


class TestLocalDriver(UnitTestsBase):
  def is_valid_connection_suggestion(self, suggestion, experiment_meta):
    experiment = LocalExperimentBuilder(experiment_meta)
    self.assert_valid_suggestion(suggestion, experiment)

  def test_driver_basic(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)

    # With experiment id
    e = conn.experiments().create(**experiment_meta)
    assert e.id == FIXED_EXPERIMENT_ID
    suggestion = conn.experiments(e.id).suggestions().create()
    self.is_valid_connection_suggestion(suggestion, experiment_meta)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    conn.experiments(e.id).observations().create(
      assignments=suggestion.assignments,
      values=values,
    )

    e2 = conn.experiments().create(**experiment_meta)
    fetched_e = conn.experiments(e2.id).fetch()
    assert e2.id == fetched_e.id
    suggestion = conn.experiments(e2.id).suggestions().create()
    self.is_valid_connection_suggestion(suggestion, experiment_meta)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    conn.experiments(e2.id).observations().create(
      suggestion=suggestion.id,
      values=values,
    )

    observations = conn.experiments(e2.id).observations().fetch()
    assert values[0]["value"] == observations.data[0].values[0].value

  def test_multiple_observations(self):
    NUM_OBSERVATIONS = 10
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    for i in range(NUM_OBSERVATIONS):
      suggestion = conn.experiments(e.id).suggestions().create()
      values = [{"name": "y1", "value": i}]
      conn.experiments(e.id).observations().create(
        assignments=suggestion.assignments,
        values=values,
      )

    observations = conn.experiments(e.id).observations().fetch()
    assert observations.count == NUM_OBSERVATIONS
    assert len(observations.data) == NUM_OBSERVATIONS

  def test_bad_route(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    # Without experiment id
    conn.experiments().create(**experiment_meta)
    with pytest.raises(Exception):
      conn.experiments().suggestions().fetch()

  @pytest.mark.parametrize("bad_id", [None, "12345", "nondigit", {}, 1])
  def test_bad_experiment_id(self, bad_id):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    experiment = conn.experiments().create(**experiment_meta)
    conn.experiments(experiment.id).suggestions().create()
    with pytest.raises(Exception):
      conn.experiments(bad_id).suggestions().create()

  def test_suggestion_duplicates(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    # Without experiment id
    e = conn.experiments().create(**experiment_meta)
    s1 = conn.experiments(e.id).suggestions().create()
    s2 = conn.experiments(e.id).suggestions().create()
    assert s1 == s2

  def test_pass_suggestion_by_id(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    s = conn.experiments(e.id).suggestions().create()
    conn.experiments(e.id).observations().create(
      suggestion=s.id,
      values=[{"name": "y1", "value": 1}],
    )
    observations = conn.experiments(e.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments == s.assignments

  def test_pass_suggestion_by_same_assignments(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)

    e = conn.experiments().create(**experiment_meta)
    s = conn.experiments(e.id).suggestions().create()
    conn.experiments(e.id).observations().create(
      assignments=s.assignments,
      values=[{"name": "y1", "value": 1}],
    )
    observations = conn.experiments(e.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments == s.assignments

  def test_pass_suggestion_by_different_assignments(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)

    e = conn.experiments().create(**experiment_meta)
    s = conn.experiments(e.id).suggestions().create()
    real_assignments = s.assignments
    real_assignments["d1"] = 1.23456789
    conn.experiments(e.id).observations().create(
      assignments=real_assignments,
      values=[{"name": "y1", "value": 1}],
    )
    observations = conn.experiments(e.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments != s.assignments
    assert stored_observation.assignments == real_assignments

  def test_old_suggestion_cleared_by_observation_different_assignments(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)

    e = conn.experiments().create(**experiment_meta)
    s = conn.experiments(e.id).suggestions().create()
    real_assignments = s.assignments
    real_assignments["d1"] = 1.23456789
    conn.experiments(e.id).observations().create(
      assignments=real_assignments,
      values=[{"name": "y1", "value": 1}],
    )

    s_new = conn.experiments(e.id).suggestions.create()
    assert s.assignments != s_new.assignments

  def test_suggestion_wrong_id(self):
    experiment_meta = self.get_experiment_feature("default")

    conn = Connection(driver=LocalDriver)
    # Without experiment id
    e = conn.experiments().create(**experiment_meta)
    s = conn.experiments(e.id).suggestions().create()
    with pytest.raises(Exception):
      conn.experiments(e.id).observations().create(
        suggestion=s.id + "1",
        values=[{"name": "y1", "value": 1}],
      )

  def test_progress(self):
    num_obs = 3
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"

    conn = Connection(driver=LocalDriver)
    # Without experiment id
    e = conn.experiments().create(**experiment_meta)
    assert e.progress.observation_count == e.progress.observation_budget_consumed == 0
    for i in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )
      e = conn.experiments(e.id).fetch()
      assert e.progress.observation_count == e.progress.observation_budget_consumed == i + 1

    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta["type"] = "random"
    e = conn.experiments().create(**experiment_meta)
    assert e.progress.observation_count == e.progress.observation_budget_consumed == 0
    for i in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )
      e = conn.experiments(e.id).fetch()
    assert e.progress.observation_count == num_obs
    assert e.progress.observation_budget_consumed <= e.progress.observation_count

  def test_best_assignments(self):
    num_obs = 10
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    for i in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )

    best_assignments = conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 1
    assert len(best_assignments.data) == 1
    assert best_assignments.data[0].values[0].value == num_obs - 1

    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["type"] = "random"

    conn = Connection(driver=LocalDriver)
    e = conn.experiments().create(**experiment_meta)
    for _ in range(num_obs):
      suggestion = conn.experiments(e.id).suggestions().create()
      conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": numpy.random.rand()}, {"name": "y2", "value": numpy.random.rand()}],
      )

    best_assignments = conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count >= 1
    assert len(best_assignments.data) >= 1
