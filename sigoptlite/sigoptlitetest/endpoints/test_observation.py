# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random
import sys

import pytest
from sigopt import Connection
from sigopt.exception import SigOptException

from sigoptlite.driver import FIXED_EXPERIMENT_ID, LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


DEFAULT_MULTIPLE_OBSERVATION_VALUES = [
  {"name": "y1", "value": 1.1, "value_stddev": 0.1},
  {"name": "y2", "value": 2.2, "value_stddev": 0.2},
]


class ObservationEndpointTest(UnitTestsBase):
  @pytest.fixture(scope="function")
  def connection(self):
    return Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment(self, connection):
    experiment_meta = self.get_experiment_feature("simple")
    yield connection.experiments().create(**experiment_meta)

  @pytest.fixture
  def suggestion(self, connection, experiment):
    return connection.experiments(experiment.id).suggestions().create()

  def create_observation_endpoint(
    self, connection, experiment, assignments=None, values=None, suggestion_id=None, use_suggestion_id=False
  ):
    if use_suggestion_id:
      assert suggestion_id is not None
      return (
        connection.experiments(experiment.id)
        .observations()
        .create(
          suggestion=suggestion_id,
          values=values,
        )
      )
    assert (assignments is not None) and (values is not None)
    return (
      connection.experiments(experiment.id)
      .observations()
      .create(
        assignments=assignments,
        values=values,
      )
    )


class TestObservationCreate(ObservationEndpointTest):
  def test_make_observation_fails_without_assignments_or_id(self, connection, experiment):
    with pytest.raises(SigOptException) as exception_info:
      connection.experiments(experiment.id).observations().create()
    msg = "Need to pass in an assignments dictionary or a suggestion id to create an observation"
    assert exception_info.value.args[0] == msg

  def test_make_observation_with_variance(self, connection, experiment, suggestion):
    value_stddev = 0.12345
    values = [{"name": "y1", "value": 0, "value_stddev": value_stddev}]
    connection.experiments(experiment.id).observations().create(
      assignments=suggestion.assignments,
      values=values,
    )
    observations = connection.experiments(experiment.id).observations().fetch()
    observation = list(observations.iterate_pages())[0]
    assert observation.values[0].value_stddev == value_stddev

  def test_observation_create_before_experiment_create(self, connection):
    with pytest.raises(SigOptException) as exception_info:
      connection.experiments(FIXED_EXPERIMENT_ID).observations().create()
    msg = "Need to create an experiment first before creating an observation"
    assert exception_info.value.args[0] == msg

  def test_observation_fetch_before_experiment_create(self, connection):
    with pytest.raises(SigOptException) as exception_info:
      connection.experiments(FIXED_EXPERIMENT_ID).observations().fetch()
    msg = "Need to create an experiment first before fetching observations"
    assert exception_info.value.args[0] == msg


class TestSingleMetricObservationEndpoint(ObservationEndpointTest):
  def test_empty_observations(self, connection, experiment):
    obs = connection.experiments(experiment.id).observations().fetch()
    assert obs.count == 0
    assert len(obs.data) == 0

  @pytest.mark.parametrize(
    "value",
    [
      0.0,
      5.1,
      sys.float_info.max,
      sys.float_info.min,
      -sys.float_info.max,
      -sys.float_info.min,
    ],
  )
  def test_create_observation_with_suggestion(self, connection, experiment, suggestion, value):
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": value}],
      )
    )
    assert observation.values[0].value == value
    assert observation.values[0].value_stddev is None
    assert observation.assignments == suggestion.assignments
    assert observation.failed is False

  @pytest.mark.parametrize(
    "observation_meta",
    [
      dict(values=[{"value": 5.1}], suggestion=0),
      dict(values=[{"value": 5.1}], suggestion=None),
      dict(values=[{"value": 5.1}]),
    ],
  )
  def test_create_invalid_suggestion(self, connection, experiment, observation_meta):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(**observation_meta)
    assert connection.experiments(experiment.id).observations().fetch().count == 0

  def test_create_observation_with_assignments(self, connection, experiment, suggestion):
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[{"name": "y1", "value": 5.1}],
        assignments=suggestion.assignments,
      )
    )
    assert observation.values[0].value == 5.1
    assert observation.values[0].value_stddev is None
    assert observation.assignments == suggestion.assignments
    assert observation.failed is False

  @pytest.mark.parametrize(
    "observation_meta",
    [
      dict(values=[{"name": "y1", "value": 5.1}], assignments=dict()),
      dict(values=[{"name": "y1", "value": 5.1}], assignments=None),
      dict(values=[{"name": "y1", "value": 5.1}], assignments=dict(x=0.0)),
      dict(values=[{"name": "y1", "value": 5.1}], assignments=dict(y=0.0)),
      dict(values=[{"name": "y1", "value": 5.1}], assignments=dict(x=0.0, y=0.0, fake=0.0)),
    ],
  )
  def test_create_observation_invalid_assignments(self, connection, experiment, observation_meta):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(**observation_meta)

  def test_create_observation_with_suggestion_and_assignments(self, connection, experiment, suggestion):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        assignments=suggestion.assignments,
        values=[{"name": "y1", "value": 2.6}],
      )

  def test_create_observation_unknown_keys(self, connection, experiment, suggestion):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": 2.6}],
        foo="bar",
      )

  def test_create_observation_nested_unknown_keys(self, connection, experiment, suggestion):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": 2.6, "foo": "bar"}],
      )

  def test_create_observation_with_failure_no_value(self, connection, experiment, suggestion):
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        failed=True,
      )
    )
    assert not observation.values
    assert observation.assignments == suggestion.assignments
    assert observation.failed is True

  def test_create_observation_with_failure_with_value(self, connection, experiment, suggestion):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(
        values=[{"name": "y1", "value": 123}],
        suggestion=suggestion.id,
        failed=True,
      )

  @pytest.mark.parametrize(
    "failed_params",
    [
      {},
      {"failed": False},
    ],
  )
  @pytest.mark.parametrize(
    "values_params",
    [
      {},
      {"values": None},
      {"values": []},
    ],
  )
  def test_create_observation_without_failure_or_values(
    self, connection, experiment, suggestion, failed_params, values_params
  ):
    with pytest.raises(SigOptException):
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        **failed_params,
        **values_params,
      )

  def test_multiple_observations(self, connection):
    num_observations = 7
    experiment_meta = self.get_experiment_feature("simple")

    e = connection.experiments().create(**experiment_meta)
    for i in range(num_observations):
      observation = (
        connection.experiments(e.id)
        .observations()
        .create(
          assignments={"d1": 0.5 + i, "i1": 10 + i},
          values=[{"name": "y1", "value": i}],
        )
      )
      assert observation.assignments["d1"] == 0.5 + i
      assert observation.assignments["i1"] == 10 + i
      assert observation.values[0].value == i

    observations = connection.experiments(e.id).observations().fetch()
    assert observations.count == num_observations
    assert len(observations.data) == num_observations
    for i, obs in enumerate(observations.data):
      assert obs.assignments["d1"] == 0.5 + i
      assert obs.assignments["i1"] == 10 + i
      assert obs.values[0].value == i

  @pytest.mark.parametrize(
    "feature",
    [
      "constraints",
      "conditionals",
      "default",
      "multisolution",
      "priors",
    ],
  )
  def test_single_metric_observations(self, connection, feature):
    num_observations = 4
    experiment_meta = self.get_experiment_feature(feature)

    e = connection.experiments().create(**experiment_meta)
    assert len(e.metrics) == 1
    metric_name = e.metrics[0].name

    assignments_list = []
    values_list = []
    for i in range(num_observations):
      suggestion = connection.experiments(e.id).suggestions().create()
      assignments = suggestion.assignments
      values = [{"name": metric_name, "value": i}]
      observation = self.create_observation_endpoint(
        connection=connection,
        experiment=e,
        assignments=assignments,
        values=values,
        suggestion_id=suggestion.id,
        use_suggestion_id=i % 2,
      )
      for param, param_value in assignments.items():
        assert observation.assignments[param] == param_value
      assert len(observation.values) == 1
      assert observation.values[0].name == metric_name
      assert observation.values[0].value == i
      assignments_list.append(assignments)
      values_list.append(values)

    observations = connection.experiments(e.id).observations().fetch()
    assert observations.count == num_observations
    assert len(observations.data) == num_observations
    for obs, params, vals in zip(observations.data, assignments_list, values_list):
      for p in params.keys():
        assert obs.assignments[p] == params[p]
      assert obs.values[0].name == vals[0]["name"]
      assert obs.values[0].value == vals[0]["value"]

  def test_assignments_observations_log_transform_bounds(self, connection):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parameters"] = [
      dict(name="x1", type="double", bounds=dict(min=1, max=100), transformation="log"),
    ]
    e = connection.experiments().create(**experiment_meta)

    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        assignments=dict(x1=-1),
        values=[{"name": "y1", "value": 1.23}],
      )

    observation = (
      connection.experiments(e.id)
      .observations()
      .create(
        assignments=dict(x1=0.5),
        values=[{"name": "y1", "value": 1.23}],
      )
    )
    assert observation is not None

  def test_out_of_bounds_observations_int_and_doubles(self, connection):
    experiment_meta = self.get_experiment_feature("default")
    e = connection.experiments().create(**experiment_meta)
    assignments = {"d1": -100, "i1": 100, "c1": "a", "l1": 1e-05, "g1": 0.1}
    observation = (
      connection.experiments(e.id)
      .observations()
      .create(
        assignments=assignments,
        values=[{"name": "y1", "value": 0}],
      )
    )
    assert dict(observation.assignments) == assignments

  def test_out_of_bounds_observations_categoricals(self, connection):
    experiment_meta = self.get_experiment_feature("default")
    e = connection.experiments().create(**experiment_meta)
    assignments = {"d1": -100, "i1": 100, "c1": "e", "l1": 1e-05, "g1": 0.1}
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        assignments=assignments,
        values=[{"name": "y1", "value": 0}],
      )

  def test_out_of_bounds_observations_grid(self, connection):
    experiment_meta = self.get_experiment_feature("default")
    e = connection.experiments().create(**experiment_meta)
    assignments = {"d1": -100, "i1": 100, "c1": "a", "l1": 1e-05, "g1": -0.1}
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        assignments=assignments,
        values=[{"name": "y1", "value": 0}],
      )

  def test_out_of_bounds_observations_conditionals(self, connection):
    experiment_meta = self.get_experiment_feature("conditionals")
    e = connection.experiments().create(**experiment_meta)

    valid_assignments = {"a": 11, "b": -18, "x": "5"}
    connection.experiments(e.id).observations().create(
      assignments=valid_assignments,
      values=[{"name": "metric", "value": 0}],
    )

    bad_assignments = {"a": 11, "b": -18, "x": "21"}
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        assignments=bad_assignments,
        values=[{"name": "metric", "value": 0}],
      )


class TestMultipleMetricObservationEndpoint(ObservationEndpointTest):
  @pytest.mark.parametrize(
    "feature",
    [
      "multimetric",
      "metric_constraint",
      "metric_threshold",
      "search",
    ],
  )
  def test_multiple_metrics_observations(self, connection, feature):
    num_observations = 4
    experiment_meta = self.get_experiment_feature(feature)

    e = connection.experiments().create(**experiment_meta)
    assert len(e.metrics) == 2

    assignments_list = []
    values_list = []
    for i in range(num_observations):
      suggestion = connection.experiments(e.id).suggestions().create()
      assignments = dict(suggestion.assignments)
      values = [{"name": "y1", "value": i}, {"name": "y2", "value": 200 + i}]
      random.shuffle(values)

      observation = self.create_observation_endpoint(
        connection=connection,
        experiment=e,
        assignments=assignments,
        values=values,
        suggestion_id=suggestion.id,
        use_suggestion_id=i % 2,
      )
      for param, param_value in assignments.items():
        assert observation.assignments[param] == param_value
      assert len(observation.values) == 2
      assert observation.values[0].name == "y1"
      assert observation.values[0].value == i
      assert observation.values[1].name == "y2"
      assert observation.values[1].value == 200 + i
      assignments_list.append(assignments)
      values_list.append(values)

    observations = connection.experiments(e.id).observations().fetch()
    assert observations.count == num_observations
    assert len(observations.data) == num_observations
    for i, (obs, params) in enumerate(zip(observations.data, assignments_list)):
      for p in params.keys():
        assert obs.assignments[p] == params[p]
      assert obs.values[0].name == "y1"
      assert obs.values[0].value == i
      assert obs.values[1].name == "y2"
      assert obs.values[1].value == 200 + i

  def test_create_observation_with_too_few_values(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        values=[{"name": "y1", "value": 6}],
        suggestion=suggestion.id,
      )

  def test_create_observation_invalid_values(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    with pytest.raises(SigOptException) as msg:
      connection.experiments(e.id).observations().create(
        values=[1, 2],
        suggestion=suggestion.id,
      )
    assert "Invalid type for" in str(msg.value)

  def test_create_multiple_values(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    observation = (
      connection.experiments(e.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        values=DEFAULT_MULTIPLE_OBSERVATION_VALUES,
      )
    )
    assert observation.values
    assert observation.assignments == suggestion.assignments

  def test_cannot_create_with_duplicate_names(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": 1.1}, {"name": "y1", "value": 1.1}],
      )

  def test_cannot_create_with_wrong_number_of_values(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[{"name": "y1", "value": 1.0}, {"name": "y2", "value": 1.0}, {"name": "y3", "value": 1.0}],
      )

  def test_cannot_create_with_wrong_names(self, connection):
    experiment_meta = self.get_experiment_feature("multimetric")
    e = connection.experiments().create(**experiment_meta)
    suggestion = connection.experiments(e.id).suggestions().create()
    with pytest.raises(SigOptException):
      connection.experiments(e.id).observations().create(
        suggestion=suggestion.id, values=[{"name": "value2", "value": 1.0}, {"name": "value3", "value": 1.0}]
      )
