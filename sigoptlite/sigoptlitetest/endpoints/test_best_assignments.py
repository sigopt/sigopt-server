# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
import random

import numpy
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_PARAMETERS


DEFAULT_NUM_RANDOM = 10


class TestBestAssignmentsLogger(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @staticmethod
  def assert_best_assignments_are_sorted(experiment, best_assignments):
    metric_values = [best_assignment.values[0].value for best_assignment in best_assignments]

    if experiment.metrics[0].objective == "minimize":
      assert sorted(metric_values) == metric_values
    else:
      assert sorted(metric_values, reverse=True) == metric_values

  @staticmethod
  def assert_best_assignments_match_observation_data(best_assignments, assignments_list, values_list):
    assert len(best_assignments) == len(assignments_list) == len(values_list)

    for assignments, values in zip(assignments_list, values_list):
      matching_index = next(i for i, best in enumerate(best_assignments) if best.assignments == assignments)
      best = best_assignments[matching_index]
      assert best.assignments == assignments
      for seen_value, expected_value in zip(best.values, values):
        assert seen_value.name == expected_value["name"]
        assert seen_value.value == expected_value["value"]

  @staticmethod
  def create_values_in_simplex(on_boundary=False, num=DEFAULT_NUM_RANDOM):
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

  @staticmethod
  def generate_random_assignments(experiment_meta, num=DEFAULT_NUM_RANDOM):
    temp_conn = Connection(driver=LocalDriver)
    temp_meta = copy.deepcopy(experiment_meta)
    temp_meta["type"] = "random"
    e = temp_conn.experiments().create(**temp_meta)
    assignments = []
    for _ in range(num):
      suggestion = temp_conn.experiments(e.id).suggestions().create()
      temp_conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name=f"y{i+1}", value=1) for i in range(len(temp_meta["metrics"]))],
      )
      assignments.append(suggestion.assignments)
    return assignments

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
    assignments_list = self.generate_random_assignments(experiment_meta, num=num_observations)
    idx = numpy.random.randint(num_observations)
    values_list[idx] = [dict(name="y1", value=best_value)]

    for assignments, values in zip(assignments_list, values_list):
      self.conn.experiments(e.id).observations().create(
        assignments=assignments,
        values=values,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == 1
    assert best_assignments_list[0].values[0].value == best_value
    assert best_assignments_list[0].assignments == assignments_list[idx]

  def test_multimetric(self):
    experiment_meta = self.get_experiment_feature("multimetric")
    experiment_meta["type"] = "random"
    e = self.conn.experiments().create(**experiment_meta)

    num_optimal = 12
    pareto_optimal_assignments = self.generate_random_assignments(experiment_meta, num=num_optimal)
    non_optimal_assignments = self.generate_random_assignments(experiment_meta, num=num_optimal)
    assignments_list = pareto_optimal_assignments + non_optimal_assignments

    pareto_optimal_values = self.create_values_in_simplex(on_boundary=True, num=num_optimal)
    non_optimal_values = self.create_values_in_simplex(on_boundary=False)
    values_list = pareto_optimal_values + non_optimal_values

    for assignments, values in sorted(zip(assignments_list, values_list), key=lambda _: random.random()):
      self.conn.experiments(e.id).observations().create(
        assignments=assignments,
        values=values,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == num_optimal

    self.assert_best_assignments_are_sorted(e, best_assignments_list)
    self.assert_best_assignments_match_observation_data(
      best_assignments_list, pareto_optimal_assignments, pareto_optimal_values
    )

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
    pareto_optimal_assignments = self.generate_random_assignments(experiment_meta, num=num_optimal)
    non_optimal_assignments = self.generate_random_assignments(experiment_meta, num=num_optimal)
    assignments_list = pareto_optimal_assignments + non_optimal_assignments

    pareto_optimal_values = self.create_values_in_simplex(on_boundary=True, num=num_optimal)
    non_optimal_values = self.create_values_in_simplex(on_boundary=False)
    values_list = pareto_optimal_values + non_optimal_values

    for assignments, values in sorted(zip(assignments_list, values_list), key=lambda _: random.random()):
      self.conn.experiments(e.id).observations().create(
        assignments=assignments,
        values=values,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    self.assert_best_assignments_are_sorted(e, best_assignments_list)

    if threshold_y1 is None:
      threshold_y1 = 0
    if threshold_y2 is None:
      threshold_y2 = 0
    for best_assignment in best_assignments_list:
      best_values = [dict(name=value.name, value=value.value) for value in best_assignment.values]
      if best_values[0]["value"] >= threshold_y1 and best_values[1]["value"] <= threshold_y2:
        assert best_values in pareto_optimal_values
      else:
        assert best_values not in pareto_optimal_values

  def test_metric_constraints(self):
    experiment_meta = self.get_experiment_feature("metric_constraint")
    experiment_meta["type"] = "random"
    threshold = experiment_meta["metrics"][0]["threshold"]
    e = self.conn.experiments().create(**experiment_meta)

    num_observations = 25
    for _ in range(num_observations):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name="y1", value=numpy.random.rand()), dict(name="y2", value=numpy.random.rand())],
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == 1
    best_observation = best_assignments_list[0]
    assert best_observation.values[0].value >= threshold

    observations = self.conn.experiments(e.id).observations().fetch()
    observations_list = list(observations.iterate_pages())
    optimized_values_within_threshold = []
    for observation in observations_list:
      if observation.values[0].value >= threshold:
        optimized_values_within_threshold.append(observation.values[1].value)

    for optimized_value in optimized_values_within_threshold:
      assert best_observation.values[1].value <= optimized_value

  def test_multimetric_search(self):
    experiment_meta = self.get_experiment_feature("search")
    experiment_meta["type"] = "random"
    e = self.conn.experiments().create(**experiment_meta)

    num_observations = 25
    for _ in range(num_observations):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name="y1", value=numpy.random.rand()), dict(name="y2", value=numpy.random.rand())],
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    self.assert_best_assignments_are_sorted(e, best_assignments_list)
    assert len(best_assignments_list) > 1

    for best_assignment in best_assignments_list:
      for i, metric in enumerate(experiment_meta["metrics"]):
        assert metric["name"] == best_assignment.values[i].name
        if metric["objective"] == "maximize":
          assert best_assignment.values[i].value >= metric["threshold"]
        if metric["objective"] == "minimize":
          assert best_assignment.values[i].value <= metric["threshold"]

  def test_multitask(self):
    experiment_meta = self.get_experiment_feature("multitask")
    experiment_meta["type"] = "random"
    e = self.conn.experiments().create(**experiment_meta)

    wrong_optimal_value = 200
    num_observations = 25
    for _ in range(num_observations):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      if suggestion.task.cost < 1:
        values = [dict(name="y1", value=wrong_optimal_value)]
      else:
        values = [dict(name="y1", value=numpy.random.rand())]
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=values,
        task=suggestion.task,
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == 1
    assert best_assignments_list[0].values[0].value <= 1

  def test_multisolutions(self):
    experiment_meta = self.get_experiment_feature("multisolution")
    experiment_meta["type"] = "random"
    num_solutions = experiment_meta["num_solutions"]
    e = self.conn.experiments().create(**experiment_meta)

    initial_values = [[dict(name="y1", value=numpy.random.rand())] for _ in range(num_solutions)]
    initial_assignments = self.generate_random_assignments(experiment_meta, num=num_solutions)
    for i in range(num_solutions):
      self.conn.experiments(e.id).observations().create(
        assignments=initial_assignments[i],
        values=initial_values[i],
      )
      best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
      best_assignments_list = list(best_assignments.iterate_pages())
      self.assert_best_assignments_match_observation_data(
        best_assignments_list, initial_assignments[: i + 1], initial_values[: i + 1]
      )

    for i in range(100):
      suggestion = self.conn.experiments(e.id).suggestions().create()
      self.conn.experiments(e.id).observations().create(
        suggestion=suggestion.id,
        values=[dict(name="y1", value=numpy.random.rand())],
      )

    best_assignments = self.conn.experiments(e.id).best_assignments().fetch()
    best_assignments_list = list(best_assignments.iterate_pages())
    assert len(best_assignments_list) == num_solutions
