# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus

import pytest

from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.base import RaisesApiException
from integration.v1.constants import EXPERIMENT_META_SEARCH
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase
from libsigopt.aux.constant import DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS


class SearchExperimentsTestBase(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self, connection):
    return deepcopy(EXPERIMENT_META_SEARCH)

  def batch_create_suggestions_observations(
    self, connection, experiment, num_obs, metric1_value, metric2_value=None, no_optimize=True
  ):
    if metric2_value is None:
      metric2_value = -metric1_value
    suggestions = []
    observations = []
    for _ in range(num_obs):
      suggestions.append(connection.experiments(experiment.id).suggestions().create())
      observations.append(
        {
          "suggestion": suggestions[-1].id,
          "values": [
            dict(name="constraint-1", value=metric1_value),
            dict(name="constraint-2", value=metric2_value),
          ],
        }
      )
    self.batch_upload_observations(experiment, observations, no_optimize=no_optimize)
    return suggestions, observations


class TestCreateSearchObservations(SearchExperimentsTestBase):
  def test_create_observation_search(self, connection, client_id, meta):
    experiment = connection.clients(client_id).experiments().create(**meta)
    suggestion = connection.experiments(experiment.id).suggestions().create()
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        suggestion=suggestion.id,
        values=[
          dict(name="constraint-1", value=0.1),
          dict(name="constraint-2", value=-8.2),
        ],
      )
    )
    assert observation.values[0].name == "constraint-1"
    assert observation.values[0].value == 0.1
    assert observation.values[1].name == "constraint-2"
    assert observation.values[1].value == -8.2


class TestCreateSearchExperiments(SearchExperimentsTestBase):
  def test_experiment_create_meta(self, connection, client_id, meta):
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id is not None
    assert e.type == "offline"
    assert e.observation_budget is not None

  def test_search_create_any_experiment(self, connection):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="constraint-1", strategy="constraint", threshold=0.1),
        dict(name="constraint-2", strategy="constraint", threshold=0.2),
      ],
      observation_budget=10,
    )
    assert e.id
    assert e.type == "offline"
    assert e.observation_budget == 10

  def test_search_update_experiment(self, connection):
    e = connection.create_any_experiment(
      metrics=[
        dict(name="constraint-1", strategy="constraint", threshold=0.1),
        dict(name="constraint-2", strategy="constraint", threshold=0.2),
      ],
      observation_budget=10,
    )
    assert e.metrics[0].threshold == 0.1
    assert e.metrics[1].threshold == 0.2
    update_experiment = connection.experiments(e.id).update(
      metrics=[
        dict(
          name="constraint-1",
          threshold=100,
        ),
        dict(
          name="constraint-2",
          threshold=1.5,
        ),
      ]
    )
    assert update_experiment.metrics[0].threshold == 100
    assert update_experiment.metrics[1].threshold == 1.5

  def test_search_create_single_metric(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        name="search simple",
        parameters=[
          {"name": "d", "type": "double", "bounds": {"min": 0, "max": 1}},
          {"name": "i", "type": "int", "bounds": {"min": -4, "max": 3}},
        ],
        metrics=[dict(name="constraint-1", strategy="constraint", threshold=0.1)],
        observation_budget=10,
      )
    )
    assert e.id
    assert e.type == "offline"
    assert e.observation_budget == 10

  def test_search_create_any_experiment_invalid_threshold(self, connection):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.create_any_experiment(
        metrics=[
          dict(name="constraint-1", strategy="constraint", threshold=None),
          dict(name="constraint-2", strategy="constraint", threshold=0.2),
        ],
        observation_budget=60,
      )

  def test_create_fails_high_number_of_dimensions(self, connection, client_id, meta):
    meta["parameters"] = [meta["parameters"][1]] * 51
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_create_fails_no_budget(self, connection, client_id, meta):
    meta.pop("observation_budget")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_create_parameter_constraints(self, connection, client_id, meta):
    meta["linear_constraints"] = [
      {"type": "less_than", "threshold": 1, "terms": [{"name": "a", "weight": 1}, {"name": "b", "weight": 1}]}
    ]
    e = connection.clients(client_id).experiments().create(**meta)
    assert e.id
    assert e.type == "offline"

  def test_create_fails_multi_task(self, connection, client_id, meta):
    meta["tasks"] = [
      {"name": "cheapest", "cost": 0.1},
      {"name": "cheaper", "cost": 0.3},
      {"name": "expensive", "cost": 1.0},
    ]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)


class TestSearchEngine(SearchExperimentsTestBase):
  def test_suggestions(self, connection, client_id, meta, services):
    e = connection.clients(client_id).experiments().create(**meta)
    num_obs, value = 16, 0.12
    suggestions, observations = self.batch_create_suggestions_observations(
      connection,
      e,
      num_obs,
      value,
      no_optimize=False,
    )
    assert len(suggestions) == len(observations) == 16
    assert len(observations[-1]["values"]) == 2

    suggestion = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.SEARCH

  def test_spe_search_suggestions(self, connection, client_id, meta, services):
    dimension = DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS + 1
    budget = 3 * dimension
    params = [{"name": str(i), "type": "double", "bounds": {"min": 1, "max": 2}} for i in range(dimension - 1)] + [
      {"name": "categorical", "type": "categorical", "categorical_values": [{"name": "a"}, {"name": "b"}]},
    ]
    meta.update({"parameters": params})
    meta.update({"observation_budget": budget})

    e = connection.clients(client_id).experiments().create(**meta)
    num_obs, value = budget, 0.12
    suggestions, observations = self.batch_create_suggestions_observations(
      connection,
      e,
      num_obs,
      value,
      no_optimize=False,
    )
    assert len(suggestions) == len(observations) == budget
    assert len(observations[-1]["values"]) == 2

    suggestion = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
    assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.SPE_SEARCH


class TestSearchBestAssignments(SearchExperimentsTestBase):
  def test_best_assignments_all_within_thresholds(self, connection, client_id, meta):
    e = connection.clients(client_id).experiments().create(**meta)
    num_obs, metric1_value, metric2_value = 12, 5.2, 6.1
    self.batch_create_suggestions_observations(
      connection,
      e,
      num_obs,
      metric1_value=metric1_value,
      metric2_value=metric2_value,
      no_optimize=True,
    )
    best_assignments = connection.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == num_obs
    for data in best_assignments.data:
      assert data.value is None
      assert data.value_stddev is None
      assert len(data.values) == 2
      assert [v.value for v in data.values] == [metric1_value, metric2_value]

  def test_create_sigle_metric_suggestions_and_observations(self, connection, client_id):
    meta = dict(
      name="search single metric",
      metrics=[
        dict(name="constraint-1", strategy="constraint", threshold=11),
      ],
      observation_budget=50,
      parameters=[
        dict(name="a", type="double", bounds=dict(min=0, max=1)),
        dict(name="b", type="double", bounds=dict(min=-50, max=0)),
        dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
        dict(name="e", type="int", bounds=dict(min=1, max=50)),
      ],
    )
    experiment = connection.clients(client_id).experiments().create(**meta)
    num_obs = 21
    suggestions = []
    observations = []
    for value in range(num_obs):
      suggestions.append(connection.experiments(experiment.id).suggestions().create())
      observations.append(
        {
          "suggestion": suggestions[-1].id,
          "values": [dict(name="constraint-1", value=value)],
        }
      )
    self.batch_upload_observations(experiment, observations, no_optimize=False)

    best_assignments = connection.experiments(experiment.id).best_assignments().fetch()
    assert best_assignments.count == 10
    for data in best_assignments.data:
      assert data.value is None
      assert data.value_stddev is None
      assert len(data.values) == 1
      assert 11 <= data.values[0].value < 21
      assert data.values[0].value_stddev is None

  def test_best_assignments_none_within_thresholds(self, connection, client_id, meta):
    e = connection.clients(client_id).experiments().create(**meta)
    num_obs, metric1_value, metric2_value = 8, -15, -12.5
    self.batch_create_suggestions_observations(
      connection,
      e,
      num_obs,
      metric1_value=metric1_value,
      metric2_value=metric2_value,
      no_optimize=True,
    )
    best_assignments = connection.experiments(e.id).best_assignments().fetch()
    assert best_assignments.count == 0
    assert best_assignments.data == []
