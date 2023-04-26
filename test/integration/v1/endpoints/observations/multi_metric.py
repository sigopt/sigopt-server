# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus
from typing import Any

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


DEFAULT_MULTICRITERIA_EXPERIMENT_META: dict[str, Any] = {
  "type": "offline",
  "name": "offline experiment",
  "metrics": [{"name": "value1"}, {"name": "value2"}],
  "observation_budget": 30,
  "parameters": [
    {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
    {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
    {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
  ],
}

DEFAULT_EXPERIMENT_META_NO_METRIC: dict[str, Any] = {
  "type": "offline",
  "name": "offline experiment",
  "observation_budget": 30,
  "parameters": [
    {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
    {"name": "b", "type": "double", "bounds": {"min": -50, "max": 0}},
    {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
  ],
}

DEFAULT_OBSERVATION_VALUES: list[dict[str, Any]] = [
  {"name": "value1", "value": 1.1, "value_stddev": 0.1},
  {"name": "value2", "value": 2.2, "value_stddev": 0.2},
]


class TestMultipleValueObservations(V1Base):
  """
    Test backwards compatibility of creating and updating observations
    using both new (multiple value) and old (single value) api calls
    """

  def compare_observation_values(self, observation, values):
    assert len(observation.values) == len(values)
    for o_value, value in zip(observation.values, values):
      assert o_value.name == value["name"]
      assert o_value.value == value["value"]
      assert o_value.value_stddev == value["value_stddev"]

  def test_create_observation_with_too_few_values(self, connection):
    e_meta = deepcopy(DEFAULT_MULTICRITERIA_EXPERIMENT_META)
    with connection.create_any_experiment(**e_meta) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
        connection.experiments(experiment.id).observations().create(
          values=[{"name": "value1", "value": 6}],
          suggestion=suggestion.id,
        )
      assert "must be equal" in str(e.value)

  def test_create_observation_with_legacy_value(self, connection):
    e_meta = deepcopy(DEFAULT_MULTICRITERIA_EXPERIMENT_META)
    with connection.create_any_experiment(**e_meta) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          values=[{"value": 6}],
          suggestion=suggestion.id,
        )

  def test_create_observation_with_too_many_values(self, connection):
    e_meta = deepcopy(DEFAULT_MULTICRITERIA_EXPERIMENT_META)
    e_meta["metrics"].pop(0)
    assert "value1" not in [m["name"] for m in e_meta["metrics"]]
    with connection.create_any_experiment(**e_meta) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
        connection.experiments(experiment.id).observations().create(
          values=[{"name": "value1", "value": 6}, {"name": "value2", "value": -8.1234}],
          suggestion=suggestion.id,
        )
      assert "must be equal" in str(e.value)

  def test_create_observation_invalid_values(self, connection):
    e_meta = deepcopy(DEFAULT_MULTICRITERIA_EXPERIMENT_META)
    with connection.create_any_experiment(**e_meta) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
        connection.experiments(experiment.id).observations().create(
          values=[1, 2],
          suggestion=suggestion.id,
        )
      assert "Invalid type for" in str(e.value)

  def test_create_multiple_values(self, connection, config_broker):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(suggestion=suggestion.id, values=DEFAULT_OBSERVATION_VALUES)
      )

      assert observation.values
      assert observation.suggestion == suggestion.id
      assert observation.assignments == suggestion.assignments
      assert observation.created is not None
      assert observation.metadata is None

      self.compare_observation_values(observation, DEFAULT_OBSERVATION_VALUES)

  def test_cannot_create_multiple_without_name(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id, values=[{"value": 1.1}, {"name": "value", "value": 2.2}]
        )

  def test_cannot_create_multiple_with_empty_name(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      names = [None, ""]
      for name in names:
        with RaisesApiException(HTTPStatus.BAD_REQUEST):
          connection.experiments(experiment.id).observations().create(
            suggestion=suggestion.id, values=[{"name": name, "value": 1.1}, {"name": "value", "value": 2.2}]
          )

  def test_cannot_create_with_duplicate_names(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id, values=[{"name": "value1", "value": 1.1}, {"name": "value1", "value": 1.1}]
        )

  def test_cannot_create_with_wrong_number_of_values(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id,
          values=[{"name": "value1", "value": 1.0}, {"name": "value2", "value": 1.0}, {"name": "value3", "value": 1.0}],
        )

  def test_cannot_create_with_wrong_names(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id, values=[{"name": "value2", "value": 1.0}, {"name": "value3", "value": 1.0}]
        )

  def test_cannot_update_with_wrong_name(self, connection, config_broker):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(suggestion=suggestion.id, values=[{"name": "value1", "value": 2.6}, {"name": "value2", "value": 2.2}])
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(observation.id).update(
          values=[{"name": "wrong name", "value": 2.7}]
        )

  def test_legacy_update_value_with_no_name(self, connection, config_broker):
    with connection.create_experiment(DEFAULT_EXPERIMENT_META_NO_METRIC) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 1.1}])
      )

      assert len(observation.values) == 1
      assert observation.values[0].name is None
      assert observation.values[0].value == 1.1

  def test_update_multiple_values(self, connection, config_broker):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(suggestion=suggestion.id, values=DEFAULT_OBSERVATION_VALUES)
      )
      new_values = deepcopy(DEFAULT_OBSERVATION_VALUES)
      new_values[0]["value"] = 1.2
      new_values[1]["value"] = 2.3
      updated_observation = connection.experiments(experiment.id).observations(observation.id).update(values=new_values)

      self.compare_observation_values(updated_observation, new_values)

  def test_update_observation_with_legacy_value(self, connection):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(suggestion=suggestion.id, values=DEFAULT_OBSERVATION_VALUES)
      )
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).observations(observation.id).update(values=[{"value": 6}])

  def test_update_multiple_value_vars(self, connection, config_broker):
    with connection.create_experiment(DEFAULT_MULTICRITERIA_EXPERIMENT_META) as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(suggestion=suggestion.id, values=DEFAULT_OBSERVATION_VALUES)
      )
      new_values = deepcopy(DEFAULT_OBSERVATION_VALUES)
      new_values[0]["value_stddev"] = 0.2
      new_values[1]["value_stddev"] = 0.3
      updated_observation = connection.experiments(experiment.id).observations(observation.id).update(values=new_values)

      self.compare_observation_values(updated_observation, new_values)
