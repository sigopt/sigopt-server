# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from sigopt import Connection

from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.driver import LocalDriver
from sigoptlite.models import FIXED_EXPERIMENT_ID
from sigoptlitetest.base_test import UnitTestsBase


class TestLocalDriver(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  def is_valid_default_suggestion(self, suggestion):
    experiment_meta = self.get_experiment_feature("default")
    experiment = LocalExperimentBuilder(experiment_meta)
    self.assert_valid_suggestion(suggestion, experiment)

  @pytest.fixture
  def default_experiment(self):
    experiment_meta = self.get_experiment_feature("default")
    e = self.conn.experiments().create(**experiment_meta)
    return e

  def test_driver_basic(self, default_experiment):
    assert default_experiment.id == FIXED_EXPERIMENT_ID
    suggestion = self.conn.experiments(default_experiment.id).suggestions().create()
    self.is_valid_default_suggestion(suggestion)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    self.conn.experiments(default_experiment.id).observations().create(
      assignments=suggestion.assignments,
      values=values,
    )

    experiment_meta = self.get_experiment_feature("default")
    e2 = self.conn.experiments().create(**experiment_meta)
    fetched_e = self.conn.experiments(e2.id).fetch()
    assert e2.id == fetched_e.id
    suggestion = self.conn.experiments(e2.id).suggestions().create()
    self.is_valid_default_suggestion(suggestion)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    self.conn.experiments(e2.id).observations().create(
      suggestion=suggestion.id,
      values=values,
    )

    observations = self.conn.experiments(e2.id).observations().fetch()
    assert values[0]["value"] == observations.data[0].values[0].value

  def test_multiple_observations(self, default_experiment):
    NUM_OBSERVATIONS = 10
    for i in range(NUM_OBSERVATIONS):
      suggestion = self.conn.experiments(default_experiment.id).suggestions().create()
      values = [{"name": "y1", "value": i}]
      self.conn.experiments(default_experiment.id).observations().create(
        assignments=suggestion.assignments,
        values=values,
      )

    observations = self.conn.experiments(default_experiment.id).observations().fetch()
    assert observations.count == NUM_OBSERVATIONS
    assert len(observations.data) == NUM_OBSERVATIONS

  def test_no_experiment_id(self):
    with pytest.raises(Exception):
      self.conn.experiments().suggestions().fetch()

  @pytest.mark.parametrize("bad_id", [None, "12345", "nondigit", {}, 1])
  def test_bad_experiment_id(self, default_experiment, bad_id):
    self.conn.experiments(default_experiment.id).suggestions().create()
    with pytest.raises(Exception):
      self.conn.experiments(bad_id).suggestions().create()

  def test_create_suggestion_twice_is_duplicates(self, default_experiment):
    s1 = self.conn.experiments(default_experiment.id).suggestions().create()
    s2 = self.conn.experiments(default_experiment.id).suggestions().create()
    assert s1 == s2

  def test_create_observation_by_id(self, default_experiment):
    s = self.conn.experiments(default_experiment.id).suggestions().create()
    self.conn.experiments(default_experiment.id).observations().create(
      suggestion=s.id,
      values=[{"name": "y1", "value": 1}],
    )
    observations = self.conn.experiments(default_experiment.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments == s.assignments

  def test_create_observation_by_same_assignments(self, default_experiment):
    s = self.conn.experiments(default_experiment.id).suggestions().create()
    self.conn.experiments(default_experiment.id).observations().create(
      assignments=s.assignments,
      values=[{"name": "y1", "value": 1}],
    )
    observations = self.conn.experiments(default_experiment.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments == s.assignments

  def test_create_observation_by_different_assignments(self, default_experiment):
    s = self.conn.experiments(default_experiment.id).suggestions().create()
    real_assignments = {"d1": 1.2345, "i1": 12, "c1": "a", "l1": 1, "g1": 0.9}
    self.conn.experiments(default_experiment.id).observations().create(
      assignments=real_assignments,
      values=[{"name": "y1", "value": 1}],
    )
    observations = self.conn.experiments(default_experiment.id).observations().fetch()
    stored_observation = next(observations.iterate_pages())
    assert stored_observation.assignments != s.assignments
    assert dict(stored_observation.assignments) == real_assignments

  def test_old_suggestion_cleared_by_new_observation_with_different_assignments(self, default_experiment):
    s = self.conn.experiments(default_experiment.id).suggestions().create()
    real_assignments = {"d1": 1.2345, "i1": 12, "c1": "a", "l1": 1, "g1": 0.9}
    self.conn.experiments(default_experiment.id).observations().create(
      assignments=real_assignments,
      values=[{"name": "y1", "value": 1}],
    )

    # Can't create a suggestion with id after creating an observation before
    with pytest.raises(ValueError):
      self.conn.experiments(default_experiment.id).observations().create(
        suggestion=s.id,
        values=[{"name": "y1", "value": 1}],
      )

    s_new = self.conn.experiments(default_experiment.id).suggestions().create()
    assert s.assignments != s_new.assignments
    assert int(s.id) + 1 == int(s_new.id)

  def test_create_suggestion_with_wrong_id_fails(self, default_experiment):
    s = self.conn.experiments(default_experiment.id).suggestions().create()
    with pytest.raises(Exception):
      self.conn.experiments(default_experiment.id).observations().create(
        suggestion=s.id + "1",
        values=[{"name": "y1", "value": 1}],
      )

  def test_progress(self):
    num_obs = 3
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"

    e = self.conn.experiments().create(**experiment_meta)
    assert e.progress.observation_count == e.progress.observation_budget_consumed == 0
    for i in range(num_obs):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )
      e = self.conn.experiments(e.id).fetch()
      assert e.progress.observation_count == e.progress.observation_budget_consumed == i + 1

    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta["type"] = "random"
    e = self.conn.experiments().create(**experiment_meta)
    assert e.progress.observation_count == e.progress.observation_budget_consumed == 0
    for i in range(num_obs):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )
      e = self.conn.experiments(e.id).fetch()
    assert e.progress.observation_count == num_obs
    assert e.progress.observation_budget_consumed <= e.progress.observation_count

  def test_best_assignments(self):
    num_obs = 10
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"

    e = self.conn.experiments().create(**experiment_meta)
    for i in range(num_obs):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": i}],
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 1
    assert len(best_assignments.data) == 1
    assert best_assignments.data[0].values[0].value == num_obs - 1

    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["type"] = "random"

    e = self.conn.experiments().create(**experiment_meta)
    for _ in range(num_obs):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": numpy.random.rand()}, {"name": "y2", "value": numpy.random.rand()}],
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count >= 1
    assert len(best_assignments.data) >= 1
