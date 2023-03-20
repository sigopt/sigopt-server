# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.constant import MetricStrategyNames

from integration.utils.make_values import make_values
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentProgress(ExperimentsTestBase):
  def assert_progress_is_not_none(self, experiment):
    assert experiment.progress is not None
    assert experiment.progress.observation_count == 0
    # TODO(SN-1197): remove the to_json() call once observation_budget_consumed is added to public API client
    assert experiment.progress.to_json()["observation_budget_consumed"] == 0
    assert experiment.progress.last_observation is None
    assert experiment.progress.first_observation is None
    assert experiment.progress.best_observation is None

  def assert_progress(self, experiment):
    assert experiment.progress.observation_count == 5
    assert experiment.progress.to_json()["observation_budget_consumed"] == 5
    assert experiment.progress.last_observation.id is not None
    assert experiment.progress.first_observation.id is not None
    assert experiment.progress.best_observation.id is not None
    assert experiment.progress.last_observation.values[0].value == 1
    assert experiment.progress.best_observation.values[0].value == 2
    assert experiment.progress.first_observation.values[0].value == -1

  def test_empty_experiment_progress(self, connection):
    with connection.create_any_experiment() as experiment:
      self.assert_progress_is_not_none(experiment)

  def test_experiment_progress(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      for i in [-1, 0, 1, 2, 1]:
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id, values=[{"value": i}], no_optimize=True
        )
      experiment = connection.experiments(experiment.id).fetch()
      self.assert_progress(experiment)

  def test_multitask_best_observation(self, connection):
    kwargs = dict(
      parameters=[dict(name="x", type="double", bounds=dict(min=0, max=100))],
      tasks=[
        dict(name="true", cost=1.0),
        dict(name="cheap", cost=0.1),
      ],
      observation_budget=10,
    )
    with connection.create_any_experiment(**kwargs) as experiment:
      connection.experiments(experiment.id).observations().create(
        assignments=dict(x=1),
        task=dict(name="cheap"),
        values=[{"value": 100}],
      )
      connection.experiments(experiment.id).observations().create(
        assignments=dict(x=2),
        task=dict(name="true"),
        values=[{"value": 1}],
      )
      experiment = connection.experiments(experiment.id).fetch()
      assert experiment.progress.best_observation is not None
      assert experiment.progress.best_observation.values[0].value == 1

  @pytest.mark.parametrize(
    "experiment_type",
    [
      "grid",
      "random",
    ],
  )
  def test_empty_experiment_progress_benchmarked(self, connection, experiment_type):
    with connection.create_any_experiment(type=experiment_type) as experiment:
      assert experiment.type == experiment_type
      self.assert_progress_is_not_none(experiment)

  @pytest.mark.parametrize(
    "experiment_type",
    [
      "grid",
      "random",
    ],
  )
  def test_experiment_progress_benchmarked(self, connection, experiment_type):
    with connection.create_any_experiment(type=experiment_type) as experiment:
      assert experiment.type == experiment_type
      suggestion = connection.experiments(experiment.id).suggestions().create()
      for i in [-1, 0, 1, 2, 1]:
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id, values=[{"value": i}], no_optimize=True
        )
      experiment = connection.experiments(experiment.id).fetch()
      self.assert_progress(experiment)

  def test_experiment_progress_objectives(self, connection, client_id, config_broker):
    min_metrics_json = [dict(name="cost", objective="minimize")]
    max_metrics_json = [dict(name="accuracy", objective="maximize")]

    e_min = connection.create_any_experiment(client_id=client_id, metrics=min_metrics_json)
    e_max = connection.create_any_experiment(client_id=client_id, metrics=max_metrics_json)

    s_min = connection.experiments(e_min.id).suggestions().create()
    s_max = connection.experiments(e_max.id).suggestions().create()
    for i in [1, 2]:
      connection.experiments(e_min.id).observations().create(
        suggestion=s_min.id, values=[{"value": i}], no_optimize=True
      )
      connection.experiments(e_max.id).observations().create(
        suggestion=s_max.id, values=[{"value": i}], no_optimize=True
      )

    e_min = connection.experiments(e_min.id).fetch()
    assert e_min.progress.best_observation.values[0].value == 1
    e_max = connection.experiments(e_max.id).fetch()
    assert e_max.progress.best_observation.values[0].value == 2

  def test_ignores_stored_metrics_as_best(self, connection, client_id, config_broker):
    metrics = [
      {"name": "a-stored-metric", "strategy": MetricStrategyNames.STORE},
      {"name": "optimized-metric"},
    ]
    e = connection.create_any_experiment(client_id=client_id, metrics=metrics)
    s = connection.experiments(e.id).suggestions().create()
    for values in [[3, 0], [1, 5]]:
      connection.experiments(e.id).observations().create(
        suggestion=s.id,
        values=make_values(e, values),
      )

    fetched_e = connection.experiments(e.id).fetch()
    assert fetched_e.progress.best_observation
    assert fetched_e.progress.best_observation.values[0].name == "a-stored-metric"
    assert fetched_e.progress.best_observation.values[0].value == 1
    assert fetched_e.progress.best_observation.values[1].value == 5
