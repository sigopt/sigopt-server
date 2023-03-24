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


class TestExperiment(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("default")

  def is_valid_connection_suggestion(self, suggestion, experiment_meta):
    experiment = LocalExperimentBuilder(experiment_meta)
    self.assert_valid_suggestion(suggestion, experiment)

  def test_driver_basic(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    assert e.id == FIXED_EXPERIMENT_ID
    suggestion = self.conn.experiments(e.id).suggestions().create()
    self.is_valid_connection_suggestion(suggestion, experiment_meta)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    self.conn.experiments(e.id).observations().create(
      assignments=suggestion.assignments,
      values=values,
    )

    e2 = self.conn.experiments().create(**experiment_meta)
    fetched_e = self.conn.experiments(e2.id).fetch()
    assert e2.id == fetched_e.id == FIXED_EXPERIMENT_ID
    suggestion = self.conn.experiments(e2.id).suggestions().create()
    self.is_valid_connection_suggestion(suggestion, experiment_meta)

    values = [{"name": "y1", "value": numpy.random.rand()}]
    self.conn.experiments(e2.id).observations().create(
      suggestion=suggestion.id,
      values=values,
    )

    observations = self.conn.experiments(e2.id).observations().fetch()
    assert values[0]["value"] == observations.data[0].values[0].value

  @pytest.mark.parametrize("bad_id", [None, "12345", "nondigit", {}, 1])
  def test_bad_experiment_id(self, experiment_meta, bad_id):
    self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(FIXED_EXPERIMENT_ID).suggestions().create()
    self.conn.experiments(int(FIXED_EXPERIMENT_ID)).suggestions().create(
      suggestion=suggestion.id,
      values=[{"name": "y1", "value": 3}],
    )
    with pytest.raises(Exception):
      self.conn.experiments(bad_id).suggestions().create()

  def test_progress(self, experiment_meta):
    num_obs = 3
    experiment_meta["type"] = "random"

    # Without experiment id
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

  def test_experiment_missing_parameters(self, experiment_meta):
    del experiment_meta["parameters"]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "Missing required json key `parameters` in sigoptlite experiment:"
    assert exception_info.value.args[0].startswith(msg)

  def test_experiment_parameters_empty_list(self, experiment_meta):
    experiment_meta["parameters"] = []
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "The length of .parameters must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_experiment_missing_metrics(self, experiment_meta):
    del experiment_meta["metrics"]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "Missing required json key `metrics` in sigoptlite experiment:"
    assert exception_info.value.args[0].startswith(msg)

  def test_experiment_metrics_empty_list(self, experiment_meta):
    experiment_meta["metrics"] = []
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "The length of .metrics must be greater than or equal to 1"
    assert exception_info.value.args[0] == msg

  def test_experiment_bad_experiment_name_type(self, experiment_meta):
    experiment_meta["name"] = 12
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**experiment_meta)
    msg = "Invalid type for .name, expected type string"
    assert exception_info.value.args[0] == msg


class TestSuggestionCreate(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("default")

  def test_suggestion_duplicates(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    s1 = self.conn.experiments(e.id).suggestions().create()
    s2 = self.conn.experiments(e.id).suggestions().create()
    assert s1 == s2

  def test_wrong_suggestion_id(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    s = self.conn.experiments(e.id).suggestions().create()
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments(e.id).observations().create(
        suggestion=s.id + "1",
        values=[{"name": "y1", "value": 1}],
      )
    msg = f"The suggestion you provided: {s.id + '1'} does not match the suggestion we stored: {s.id}"
    assert exception_info.value.args[0] == msg

  def test_no_suggestion_id(self, experiment_meta):
    self.conn.experiments().create(**experiment_meta)
    with pytest.raises(Exception) as exception_info:
      self.conn.experiments().suggestions().fetch()
    msg = "Please provide an Experiment ID."
    assert exception_info.value.args[0] == msg


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
