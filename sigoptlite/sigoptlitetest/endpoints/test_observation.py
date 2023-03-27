# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import FIXED_EXPERIMENT_ID, LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestObservationCreate(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("default")

  def test_make_observation_fails_without_assignments_or_id(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments(e.id).observations().create()
    msg = "Need to pass in an assignments dictionary or a suggestion id to create an observation"
    assert exception_info.value.args[0] == msg

  def test_make_observation_with_suggestion_id_matches_assignments(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(e.id).suggestions().create()
    true_assignments = suggestion.assignments
    self.conn.experiments(e.id).observations().create(
      suggestion=suggestion.id,
      values=[{"name": "y1", "value": 0}],
    )
    observations = self.conn.experiments(e.id).observations().fetch()
    observation = list(observations.iterate_pages())[0]
    assert observation.assignments == true_assignments

  def test_multiple_observations(self, experiment_meta):
    NUM_OBSERVATIONS = 10
    e = self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(e.id).suggestions().create()
    for i in range(NUM_OBSERVATIONS):
      values = [{"name": "y1", "value": i}]
      self.conn.experiments(e.id).observations().create(
        assignments=suggestion.assignments,
        values=values,
      )

    observations = self.conn.experiments(e.id).observations().fetch()
    assert observations.count == NUM_OBSERVATIONS
    assert len(observations.data) == NUM_OBSERVATIONS

  def test_make_observation_with_variance(self, experiment_meta):
    value_stddev = 0.12345
    e = self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(e.id).suggestions().create()
    values = [{"name": "y1", "value": 0, "value_stddev": value_stddev}]
    self.conn.experiments(e.id).observations().create(
      assignments=suggestion.assignments,
      values=values,
    )
    observations = self.conn.experiments(e.id).observations().fetch()
    observation = list(observations.iterate_pages())[0]
    assert observation.values[0].value_stddev == value_stddev

  def test_observation_create_before_experiment_create(self):
    new_conn = Connection(driver=LocalDriver)
    with pytest.raises(ValueError) as exception_info:
      new_conn.experiments(FIXED_EXPERIMENT_ID).observations().create()
    msg = "Need to create an experiment first before creating an observation"
    assert exception_info.value.args[0] == msg

  def test_observation_fetch_before_experiment_create(self):
    new_conn = Connection(driver=LocalDriver)
    with pytest.raises(ValueError) as exception_info:
      new_conn.experiments(FIXED_EXPERIMENT_ID).observations().fetch()
    msg = "Need to create an experiment first before fetching observations"
    assert exception_info.value.args[0] == msg
