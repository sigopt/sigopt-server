# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from unittest.mock import patch

import numpy
import pytest

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.misc.constant import MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
from libsigopt.compute.misc.multimetric import *
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import form_points_sampled


class TestMultimetricFiltering(NumericalTestCase):
  mixed_domain = CategoricalDomain(
    [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [3, -1, 5]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 7]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [11, 22]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
    ]
  )

  @staticmethod
  def _form_multimetric_info(method_name):
    method = method_name
    if method == CONVEX_COMBINATION:
      phase = numpy.random.choice([CONVEX_COMBINATION_RANDOM_SPREAD, CONVEX_COMBINATION_SEQUENTIAL])
      phase_kwargs = {"fraction_of_phase_completed": numpy.random.random()}
    elif method in (EPSILON_CONSTRAINT, PROBABILISTIC_FAILURES):
      phase = numpy.random.choice(
        [
          EPSILON_CONSTRAINT_OPTIMIZE_0,
          EPSILON_CONSTRAINT_OPTIMIZE_1,
        ]
      )
      phase_kwargs = {"fraction_of_phase_completed": numpy.random.random()}
    elif method == OPTIMIZING_ONE_METRIC:
      phase = numpy.random.choice(
        [
          OPTIMIZING_ONE_METRIC_OPTIMIZE_0,
          OPTIMIZING_ONE_METRIC_OPTIMIZE_1,
        ]
      )
      phase_kwargs = {}
    else:
      phase = NOT_MULTIMETRIC
      phase_kwargs = {}
    return form_multimetric_info_from_phase(phase, phase_kwargs)

  def test_form_convex_combination_weights(self):
    budget = numpy.random.randint(50, 100)
    max_points = numpy.random.randint(10, 50) + budget
    assert all(
      all(0 <= w <= 1 for w in form_convex_combination_weights(CONVEX_COMBINATION_RANDOM_SPREAD, n / budget))
      for n in range(max_points)
    )
    assert all(
      all(0 <= w <= 1 for w in form_convex_combination_weights(CONVEX_COMBINATION_SEQUENTIAL, n / budget))
      for n in range(max_points)
    )

  def test_form_epsilon_constraint_epsilon(self):
    budget = numpy.random.randint(50, 100)
    max_points = numpy.random.randint(10, 50) + budget
    assert all(0 <= form_epsilon_constraint_epsilon(n / budget) <= 1 for n in range(max_points))

  @staticmethod
  def _create_pareto_frontier_values(count):
    values = numpy.empty((count, 2))
    values[:, 0] = numpy.linspace(0, count - 1, count)
    values[:, 1] = numpy.linspace(count - 1, 0, count)
    return values

  @staticmethod
  def _create_one_optima_values(count):
    values = numpy.empty((count, 2))
    values[:, 0] = numpy.linspace(0, count - 1, count)
    values[:, 1] = numpy.linspace(0, count - 1, count)
    return values

  def test_find_epsilon_constraint_value(self):
    epsilon = 1.1
    constraint_metric = 0
    points_sampled_values = numpy.empty((5, 2))
    with pytest.raises(AssertionError):
      find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)

    epsilon = 0
    with pytest.raises(AssertionError):
      find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)

    epsilon = numpy.random.uniform(0.1, 0.9)
    points_sampled_values = numpy.ones(5)
    with pytest.raises(AssertionError):
      find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)

    constraint_metric = 1
    points_sampled_values = numpy.ones((5, 1))
    with pytest.raises(AssertionError):
      find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)

    points_sampled_values = numpy.ones((5, 2))
    find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)

    # Only one optima
    epsilon1 = 0.3
    epsilon2 = 0.8
    points_sampled_values = numpy.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]])
    constraint_value1 = find_epsilon_constraint_value(epsilon1, constraint_metric, points_sampled_values)
    constraint_value2 = find_epsilon_constraint_value(epsilon2, constraint_metric, points_sampled_values)
    assert constraint_value1 == constraint_value2

    # All points are pareto frontier
    epsilon = 0.3
    points_sampled_values = numpy.array([[0, 5], [1, 4], [2, 3], [3, 2], [4, 1], [5, 0]])
    constraint_value = find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)
    assert constraint_value == 1.5

    epsilon = 0.7
    points_sampled_values = numpy.array([[0, 5], [numpy.nan, numpy.nan], [2, 3], [3, 2], [4, 1], [5, 0]])
    constraint_value = find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)
    assert constraint_value == 3.5

    # 2 points are pareto frontier
    constraint_metric = 0
    epsilon = 0.5
    points_sampled_values = numpy.array([[3, 4], [6, 7], [2, 1], [0, 2], [7, 3], [5, 2]])
    constraint_value = find_epsilon_constraint_value(epsilon, constraint_metric, points_sampled_values)
    assert constraint_value == 1.0

  def test_force_minimum_successful_points(self):
    margin = 2
    num_points = margin + MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
    points_sampled_values = self._create_pareto_frontier_values(num_points)

    optimizing_metric = 2
    points_sampled_failures = numpy.ones(num_points, dtype=bool)
    points_sampled_failures[margin:] = False
    with pytest.raises(AssertionError):
      force_minimum_successful_points(optimizing_metric, points_sampled_values, points_sampled_failures)

    points_sampled_failures = numpy.ones(margin, dtype=bool)
    with pytest.raises(AssertionError):
      force_minimum_successful_points(optimizing_metric, points_sampled_values, points_sampled_failures)

    optimizing_metric = 1
    points_sampled_failures = numpy.zeros(num_points, dtype=bool)
    points_sampled_failures[0] = True
    modified_points_sampled_failures = force_minimum_successful_points(
      optimizing_metric, points_sampled_values, points_sampled_failures
    )

    assert sum(modified_points_sampled_failures) == 1

    optimizing_metric = 1
    points_sampled_failures = numpy.ones(num_points, dtype=bool)
    points_sampled_failures[:margin] = False

    modified_points_sampled_failures = force_minimum_successful_points(
      optimizing_metric,
      points_sampled_values,
      points_sampled_failures,
    )

    # The best values in optimizing_metric=1 are the last points (see self._create_pareto_frontier_values())
    expected_failures = numpy.copy(points_sampled_failures)
    successful_index_from = -MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS + margin
    if successful_index_from < 0:
      expected_failures[successful_index_from:] = False

    assert sum(~modified_points_sampled_failures) == MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
    assert (modified_points_sampled_failures == expected_failures).all()

    # Test when length of points_sampled < MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
    # NOTE: This test will be skipped if MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS is 0
    num_points = MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS - 1
    if num_points > 0:
      optimizing_metric = 1
      points_sampled_failures = numpy.ones(num_points, dtype=bool)
      points_sampled_values = self._create_pareto_frontier_values(num_points)

      # NOTE: Real failures should be received as constant liar value and not as NaN
      # when this method is being executed. It can happen that those real failures are flipped as successful,
      # we will not get a good model but given that we don't have much other points to work with,
      # it shouldn't be a problem.
      modified_points_sampled_failures = force_minimum_successful_points(
        optimizing_metric,
        points_sampled_values,
        points_sampled_failures,
      )

      expected_failures = numpy.zeros(num_points, dtype=bool)

      assert len(modified_points_sampled_failures) == num_points
      assert (modified_points_sampled_failures == expected_failures).all()

  def test_filter_convex_combination(self):
    multimetric_info = self._form_multimetric_info(CONVEX_COMBINATION)
    assert isinstance(multimetric_info.params, ConvexCombinationParams)
    assert numpy.sum(multimetric_info.params.weights) == 1
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_convex_combination(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    assert (modified_points_sampled_points == points_sampled.points).all()
    for mpsv, psv in zip(modified_points_sampled_values, points_sampled.values):
      assert numpy.isclose(
        mpsv,
        multimetric_info.params.weights[0] * psv[0] + multimetric_info.params.weights[1] * psv[1],
      )
    for mpsvv, psvv in zip(modified_points_sampled_value_vars, points_sampled.value_vars):
      assert numpy.isclose(
        mpsvv,
        multimetric_info.params.weights[0] ** 2 * psvv[0] + multimetric_info.params.weights[1] ** 2 * psvv[1],
      )
    assert modified_lie_value == multimetric_info.params.weights[1]

  def test_filter_convex_combination_sum_of_gps(self):
    multimetric_info = self._form_multimetric_info(CONVEX_COMBINATION)
    assert isinstance(multimetric_info.params, ConvexCombinationParams)
    assert numpy.sum(multimetric_info.params.weights) == 1
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_convex_combination_sum_of_gps(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    assert (modified_points_sampled_points == points_sampled.points).all()
    assert (modified_points_sampled_values == points_sampled.values).all()
    assert (modified_points_sampled_value_vars == points_sampled.value_vars).all()
    assert (modified_lie_value == lie_values).all()
    assert modified_points_sampled_values.shape[1] == 2

  def test_filter_epsilon_constraint(self):
    multimetric_info = self._form_multimetric_info(EPSILON_CONSTRAINT)
    assert multimetric_info.method == EPSILON_CONSTRAINT
    assert isinstance(multimetric_info.params, ProbabilisticFailuresParams)
    assert multimetric_info.params.optimizing_metric + multimetric_info.params.constraint_metric == 1
    assert 0 <= multimetric_info.params.epsilon <= 1

    num_points = MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS * 2

    multimetric_info = MultimetricInfo(
      method=EPSILON_CONSTRAINT,
      params=ProbabilisticFailuresParams(
        epsilon=0.5,
        optimizing_metric=0,
        constraint_metric=2,
      ),
    )
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=num_points,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])

    with pytest.raises(AssertionError):
      filter_epsilon_contraint(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.value_vars,
        points_sampled.failures,
        lie_values,
      )

    multimetric_info = MultimetricInfo(
      method=EPSILON_CONSTRAINT,
      params=ProbabilisticFailuresParams(
        epsilon=0.5,
        optimizing_metric=0,
        constraint_metric=1,
      ),
    )
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=num_points,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([-77, -99])
    points_sampled.values = self._create_pareto_frontier_values(num_points)
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_epsilon_contraint(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    optimizing_metric = multimetric_info.params.optimizing_metric
    expected_values = numpy.copy(points_sampled.values[:, optimizing_metric])
    expected_values[: num_points // 2] = modified_lie_value

    assert (modified_points_sampled_points == points_sampled.points).all()
    assert (modified_points_sampled_values == expected_values).all()
    assert (modified_points_sampled_value_vars == points_sampled.value_vars[:, 0]).all()
    assert modified_lie_value == lie_values[optimizing_metric]

    multimetric_info = MultimetricInfo(
      method=EPSILON_CONSTRAINT,
      params=ProbabilisticFailuresParams(
        epsilon=0.5,
        optimizing_metric=1,
        constraint_metric=0,
      ),
    )
    points_sampled.failures = numpy.zeros(num_points, dtype=bool)
    points_sampled.failures[0] = True
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_epsilon_contraint(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    optimizing_metric = multimetric_info.params.optimizing_metric
    expected_values = numpy.copy(points_sampled.values[:, optimizing_metric])
    expected_values[points_sampled.failures] = modified_lie_value
    expected_values[num_points // 2 : -1] = modified_lie_value

    assert (modified_points_sampled_values[points_sampled.failures] == lie_values[optimizing_metric]).all()
    assert (modified_points_sampled_points == points_sampled.points).all()
    assert (modified_points_sampled_values == expected_values).all()
    assert (modified_points_sampled_value_vars == points_sampled.value_vars[:, optimizing_metric]).all()
    assert modified_lie_value == lie_values[optimizing_metric]

  def test_filter_probabilistic_failures(self):
    num_points = MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS * 2

    multimetric_info = MultimetricInfo(
      method=PROBABILISTIC_FAILURES,
      params=ProbabilisticFailuresParams(
        epsilon=0.5,
        optimizing_metric=0,
        constraint_metric=2,
      ),
    )
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=num_points,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])

    with pytest.raises(AssertionError):
      filter_probabilistic_failure(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.value_vars,
        points_sampled.failures,
        lie_values,
      )

    multimetric_info = MultimetricInfo(
      method=PROBABILISTIC_FAILURES,
      params=ProbabilisticFailuresParams(
        epsilon=0.5,
        optimizing_metric=1,
        constraint_metric=0,
      ),
    )
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=num_points,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([-77, -99])
    points_sampled.values = self._create_pareto_frontier_values(num_points)
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_probabilistic_failure(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    optimizing_metric = multimetric_info.params.optimizing_metric
    expected_values = points_sampled.values[: num_points // 2, optimizing_metric]
    expected_points = points_sampled.points[: num_points // 2, :]
    expected_value_vars = points_sampled.value_vars[: num_points // 2, optimizing_metric]

    assert (modified_points_sampled_points == expected_points).all()
    assert (modified_points_sampled_values == expected_values).all()
    assert (modified_points_sampled_value_vars == expected_value_vars).all()
    assert modified_lie_value == lie_values[optimizing_metric]

    points_sampled.failures = numpy.zeros(num_points, dtype=bool)
    points_sampled.failures[0] = True
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_probabilistic_failure(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )
    optimizing_metric = multimetric_info.params.optimizing_metric
    expected_values = points_sampled.values[: num_points // 2, optimizing_metric]
    expected_points = points_sampled.points[: num_points // 2, :]
    expected_value_vars = points_sampled.value_vars[: num_points // 2, optimizing_metric]

    assert (modified_points_sampled_points == expected_points).all()
    assert (modified_points_sampled_values == expected_values).all()
    assert (modified_points_sampled_value_vars == expected_value_vars).all()
    assert modified_lie_value == lie_values[optimizing_metric]

  # NOTE: With the adjusted epsilon bounds, all failures are more likely to occur.
  # I have added this test to be sure that we enforce some minimum amount of successful values.
  def test_filter_epsilon_constraint_all_failures(self):
    multimetric_info = MultimetricInfo(
      method=EPSILON_CONSTRAINT,
      params=ProbabilisticFailuresParams(
        epsilon=0.1,
        optimizing_metric=1,
        constraint_metric=0,
      ),
    )
    unique_lie_value = -99  # Seeing this number in modified_points_sampled_values means a failure
    point_sampled_values = self._create_one_optima_values(MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS)

    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=len(point_sampled_values),
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    points_sampled.values = point_sampled_values
    lie_values = numpy.array([0, unique_lie_value])
    (_, modified_points_sampled_values, _, _) = filter_epsilon_contraint(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )

    num_successful = sum(modified_points_sampled_values != unique_lie_value)
    assert num_successful == MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS

  # NOTE: With the adjusted epsilon bounds, all failures are more likely to occur.
  # I have added this test to be sure that we enforce some minimum amount of successful values.
  def test_filter_probabilistic_failures_all_failures(self):
    multimetric_info = MultimetricInfo(
      method=PROBABILISTIC_FAILURES,
      params=ProbabilisticFailuresParams(
        epsilon=0.1,
        optimizing_metric=1,
        constraint_metric=0,
      ),
    )
    unique_lie_value = -99  # Seeing this number in modified_points_sampled_values means a failure
    point_sampled_values = self._create_one_optima_values(MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS)

    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=len(point_sampled_values),
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    points_sampled.values = point_sampled_values
    lie_values = numpy.array([0, unique_lie_value])
    (_, modified_points_sampled_values, _, _) = filter_probabilistic_failure(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )

    num_successful = numpy.count_nonzero(modified_points_sampled_values != unique_lie_value)
    assert num_successful == MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS

  def test_filter_optimize_one_metric(self):
    multimetric_info = self._form_multimetric_info(OPTIMIZING_ONE_METRIC)
    assert multimetric_info.method == OPTIMIZING_ONE_METRIC
    assert isinstance(multimetric_info.params, OptimizeOneMetricParams)
    assert multimetric_info.params.optimizing_metric + multimetric_info.params.constraint_metric == 1
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    (
      modified_points_sampled_points,
      modified_points_sampled_values,
      modified_points_sampled_value_vars,
      modified_lie_value,
    ) = filter_optimizing_one_metric(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )

    optimizing_metric = multimetric_info.params.optimizing_metric
    assert (modified_points_sampled_points == points_sampled.points).all()
    assert (modified_points_sampled_values == points_sampled.values[:, optimizing_metric]).all()
    assert (modified_points_sampled_value_vars == points_sampled.value_vars[:, optimizing_metric]).all()
    assert modified_lie_value == lie_values[optimizing_metric]

  @pytest.mark.parametrize(
    "params",
    [
      (CONVEX_COMBINATION, "libsigopt.compute.misc.multimetric.filter_convex_combination_sum_of_gps", 123),
      (EPSILON_CONSTRAINT, "libsigopt.compute.misc.multimetric.filter_probabilistic_failure", 321),
      (OPTIMIZING_ONE_METRIC, "libsigopt.compute.misc.multimetric.filter_optimizing_one_metric", 222),
      (NOT_MULTIMETRIC, "libsigopt.compute.misc.multimetric.filter_not_multimetric", 333),
    ],
  )
  def test_filter_multimetric_points_sampled(self, params):
    phase, filter_name, expected_output = params
    multimetric_info = self._form_multimetric_info(phase)
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=1 if phase == NOT_MULTIMETRIC else 2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    with patch(filter_name) as mock:
      mock.return_value = expected_output
      output = filter_multimetric_points_sampled(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.value_vars,
        points_sampled.failures,
        lie_values,
      )
    assert output == expected_output
    mock.assert_called_once_with(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.value_vars,
      points_sampled.failures,
      lie_values,
    )

  def test_filter_multimetric_points_sampled_failed(self):
    multimetric_info = self._form_multimetric_info(PROBABILISTIC_FAILURES)
    multimetric_info = MultimetricInfo(method=PROBABILISTIC_FAILURES, params=multimetric_info.params)
    assert multimetric_info.method == PROBABILISTIC_FAILURES
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    with pytest.raises(AssertionError):
      filter_multimetric_points_sampled(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.value_vars,
        points_sampled.failures,
        lie_values,
      )

    multimetric_info = MultimetricInfo(method="something_else", params=multimetric_info.params)
    with pytest.raises(AssertionError):
      filter_multimetric_points_sampled(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.value_vars,
        points_sampled.failures,
        lie_values,
      )

  def test_filter_multimetric_points_sampled_spe_failed(self):
    multimetric_info = self._form_multimetric_info(PROBABILISTIC_FAILURES)
    multimetric_info = MultimetricInfo(method=PROBABILISTIC_FAILURES, params=multimetric_info.params)
    assert multimetric_info.method == PROBABILISTIC_FAILURES
    points_sampled = form_points_sampled(
      domain=self.mixed_domain,
      num_sampled=5,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.array([]),
      failure_prob=0,
    )
    lie_values = numpy.array([0, 1])
    with pytest.raises(AssertionError):
      filter_multimetric_points_sampled_spe(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.failures,
        lie_values,
      )

    multimetric_info = MultimetricInfo(method="something_else", params=multimetric_info.params)
    with pytest.raises(AssertionError):
      filter_multimetric_points_sampled_spe(
        multimetric_info,
        points_sampled.points,
        points_sampled.values,
        points_sampled.failures,
        lie_values,
      )
