# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import numpy
import pytest

from sigoptlite.best_assignments import BestAssignmentsLogger
from sigoptlite.builders import LocalExperimentBuilder
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_PARAMETERS
from sigoptlite.driver import LocalDriver

from sigopt import Connection


class TestBestAssignmentsLogger(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @staticmethod
  def best_assignments_to_value_list(best_assignments):
    best_values_seen = []
    for best_assignment in best_assignments:
      best_values_seen.append(
        [dict(name=value.name, value=value.value) for value in best_assignment.values]
      )
    return best_values_seen

  @staticmethod
  def assert_observation_lists_are_equal(list_1, list_2):
    assert len(list_1) == len(list_2) and all(l1 in list_2 for l1 in list_1)

  @staticmethod
  def assert_best_assignments_are_sorted(experiment, best_assignments):
    objective = experiment.metrics[0].objective

    metric_values = []
    for best_assignment in best_assignments:
      metric_values.append(best_assignment.values[0].value)

    if objective == "minimize":
      assert sorted(metric_values) == metric_values
    else:
      assert sorted(metric_values, reverse=True) == metric_values

  def create_values_in_simplex(self, on_boundary=False, num=10):
    y1_values = numpy.linspace(0, 1, num=num)
    values_list = []
    for y1 in y1_values:  # Create observations according to simplex in lower right quadrant
      y2 = y1 - 1
      alpha = 1 if on_boundary else numpy.random.uniform(low=0, high=0.8)
      best_observation_values = [
        dict(name="y1", value=alpha * y1),
        dict(name="y2", value=alpha * y2),
      ]
      values_list.append(best_observation_values)
    return values_list

  @pytest.mark.parametrize(
    "feature",
    [
      "default",
      "multimetric",
      "metric_constraint",
      "metric_threshold",
      "search",
    ],
  )
  def test_failed_observations(self, feature):
    # No observations
    experiment_meta = self.get_experiment_feature(feature)
    e = self.conn.experiments().create(**experiment_meta)
    best_observations = self.conn.experiments(e.id).best_assignments().fetch()
    best_observations_list = list(best_observations.iterate_pages())
    assert best_observations_list == []

    # All observations are failures
    for _ in range(5):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        failed=True,
      )

    best_observations = self.conn.experiments(e.id).best_assignments().fetch()
    best_observations_list = list(best_observations.iterate_pages())
    assert best_observations_list == []

  @pytest.mark.parametrize("objective, best_value", [("maximize", 100), ("minimize", -100)])
  def test_single_metric(self, objective, best_value):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["type"] = "random"
    experiment_meta["metrics"][0]["objective"] = objective
    e = self.conn.experiments().create(**experiment_meta)

    num_observations = 10
    values_list = [[dict(name="y1", value=numpy.random.rand())] for _ in range(num_observations)]
    idx = numpy.random.randint(num_observations)
    values_list[idx] = [dict(name="y1", value=best_value)]

    for values in values_list:
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=values,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == 1
    assert best_assignments_list[0].values[0].value == best_value

  def test_multimetric(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["type"] = "random"
    e = self.conn.experiments().create(**experiment_meta)

    num_optimal = 12
    pareto_optimal_values = self.create_values_in_simplex(on_boundary=True, num=num_optimal)
    non_optimal_values = self.create_values_in_simplex(on_boundary=False)
    observation_values_list = pareto_optimal_values + non_optimal_values
    assignments_list = [
      self.conn.experiments(e.id).suggestions().create().assignments for _ in range(len(observation_values_list))
    ]
    random.shuffle(observation_values_list)

    for assignments, values in zip(assignments_list, observation_values_list):
      self.conn.experiments(e.id).observations().create(
        assignments=assignments,
        values=values,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == num_optimal

    self.assert_best_assignments_are_sorted(e, best_assignments_list)
    best_values_seen = self.best_assignments_to_value_list(best_assignments_list)
    self.assert_observation_lists_are_equal(best_values_seen, pareto_optimal_values)

  # @pytest.mark.xfail
  @pytest.mark.parametrize("threshold_y1, threshold_y2", [(None, -0.25), (0.25, None), (0.25, -0.25)])
  def test_multimetric_thresholds(self, threshold_y1, threshold_y2):
    experiment_meta = dict(
      parameters=DEFAULT_PARAMETERS,
      metrics=[
        dict(name="y1", objective="maximize", threshold=threshold_y1),
        dict(name="y2", objective="minimize", threshold=threshold_y2),
      ],
      observation_budget=123,
      type="random",
    )
    e = self.conn.experiments().create(**experiment_meta)

    num_optimal = 12
    pareto_optimal_values = self.create_values_in_simplex(on_boundary=True, num=num_optimal)
    non_optimal_values = self.create_values_in_simplex(on_boundary=False)
    observation_values_list = pareto_optimal_values + non_optimal_values
    assignments_list = [
      self.conn.experiments(e.id).suggestions().create().assignments for _ in range(len(observation_values_list))
    ]
    random.shuffle(observation_values_list)

    for assignments, values in zip(assignments_list, observation_values_list):
      self.conn.experiments(e.id).observations().create(
        assignments=assignments,
        values=values,
      )

    if threshold_y1 is None:
      threshold_y1 = 0

    if threshold_y2 is None:
      threshold_y2 = 0

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())

    self.assert_best_assignments_are_sorted(e, best_assignments_list)
    best_values_seen = self.best_assignments_to_value_list(best_assignments_list)
    for best_values in best_values_seen:
      if best_values[0]["value"] >= threshold_y1 and best_values[1]["value"] <= threshold_y2:
        assert best_values in pareto_optimal_values
      else:
        assert best_values not in pareto_optimal_values

  @pytest.mark.xfail
  def test_metric_constraints(self):
    experiment_meta = self.get_experiment_feature("metric_constraint")
    assert experiment_meta["metrics"][0]["strategy"] == "constraint"
    threshold = experiment_meta["metrics"][0]["threshold"]
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = self.make_random_observations(experiment, num_observations=25)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == 1

    best_observation = best_observations_from_logger[0]
    assert best_observation["values"][0]["value"] >= threshold

    valid_observations = best_assignments_logger.filter_valid_full_cost_observations(observations)
    expected_valid_observations = [o.get_client_observation(experiment) for o in valid_observations]
    for observation in expected_valid_observations:
      assert best_observation["values"][1]["value"] <= observation["values"][1]["value"]

  @pytest.mark.xfail
  def test_multimetric_search(self):
    experiment_meta = self.get_experiment_feature("search")
    thresholds = [m["threshold"] for m in experiment_meta["metrics"]]
    objectives = [m["objective"] for m in experiment_meta["metrics"]]
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = self.make_random_observations(experiment, num_observations=25)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    self.assert_observations_are_sorted(best_observations_from_logger, experiment)

    for best_observation in best_observations_from_logger:
      for i, metric in enumerate(best_observation["values"]):
        if objectives[i] == "maximize":
          assert metric["value"] >= thresholds[i]
        if objectives[i] == "minimize":
          assert metric["value"] <= thresholds[i]

    valid_observations = best_assignments_logger.filter_valid_full_cost_observations(observations)
    expected_valid_observations = [o.get_client_observation(experiment) for o in valid_observations]
    assert len(best_observations_from_logger) > 1
    self.assert_observation_lists_are_equal(best_observations_from_logger, expected_valid_observations)

  def test_multitask(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment = LocalExperimentBuilder(experiment_meta)
    observations = []
    for _ in range(20):
      observation_with_task = self.make_observation(
        experiment=experiment,
        assignments=self.make_random_suggestions(experiment)[0].assignments,
        values=[dict(name="y1", value=numpy.random.rand())],
        task=numpy.random.choice(experiment_meta["tasks"]),
      )
      observations.append(observation_with_task)

    best_assignments_logger = BestAssignmentsLogger(experiment)
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == 1
    assert best_observations_from_logger[0]["task"]["cost"] == 1
    assert best_observations_from_logger[0]["task"]["name"] == "expensive"

  def test_multisolutions(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    num_solutions = experiment_meta["num_solutions"]
    experiment = LocalExperimentBuilder(experiment_meta)
    best_assignments_logger = BestAssignmentsLogger(experiment)
    observations = []
    for _ in range(num_solutions):
      observation = self.make_observation(
        experiment=experiment,
        assignments=self.make_random_suggestions(experiment)[0].assignments,
        values=[dict(name="y1", value=numpy.random.rand())],
      )
      observations.append(observation)
      best_observations_from_logger = best_assignments_logger.fetch(observations)
      expected_observations = [o.get_client_observation(experiment) for o in observations]
      self.assert_observation_lists_are_equal(best_observations_from_logger, expected_observations)

    observations.extend(self.make_random_observations(experiment, 100))
    best_observations_from_logger = best_assignments_logger.fetch(observations)
    assert len(best_observations_from_logger) == num_solutions
