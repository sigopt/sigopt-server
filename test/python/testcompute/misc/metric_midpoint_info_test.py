# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.compute.misc.constant import (
  CONSTANT_LIAR_MAX,
  CONSTANT_LIAR_MEAN,
  CONSTANT_LIAR_MIN,
  DEFAULT_CONSTANT_LIAR_VALUE,
)
from libsigopt.compute.misc.data_containers import MultiMetricMidpointInfo, SingleMetricMidpointInfo
from testaux.numerical_test_case import NumericalTestCase


class TestSingleMetricMidpointInfo(NumericalTestCase):
  def test_creation_skip(self):
    mmi = SingleMetricMidpointInfo(numpy.array([]), numpy.array([], dtype=bool))
    assert mmi.skip
    mmi = SingleMetricMidpointInfo(numpy.random.random(5), numpy.full(5, True, dtype=bool))
    assert mmi.skip

    assert mmi.relative_objective_value(2.3) == -2.3
    assert mmi.relative_objective_variance(2.3) == 2.3
    assert mmi.relative_objective_variance(0) > 0
    assert mmi.undo_scaling(2.3) == -2.3
    assert mmi.undo_scaling_variances(2.3) == 2.3

    unscaled_values = mmi.undo_scaling(numpy.array([1.3, 5.3]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == -numpy.array([1.3, 5.3]))

  # NOTE: This test is hard-coded to pass for scaling to [-.1, .1]
  #       This is intentional so that we think about what impact that has if we ever change it
  def test_scaling(self):
    count = 10
    mmi = SingleMetricMidpointInfo(numpy.arange(count), numpy.full(count, False, dtype=bool))
    assert not mmi.skip
    assert mmi.min == 0.0
    assert mmi.max == 9.0
    assert mmi.midpoint == 4.5
    assert mmi.scale == 0.2 / 9.0

    assert mmi.relative_objective_value(0.0) == 0.1
    assert mmi.relative_objective_value(9.0) == -0.1
    assert mmi.relative_objective_variance(0.3) == (0.2 / 9.0) ** 2 * 0.3
    assert mmi.undo_scaling(0.1) == 0.0
    assert mmi.undo_scaling(-0.1) == 9.0
    assert mmi.undo_scaling_variances((0.2 / 9.0) ** 2 * 0.3) == 0.3

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([0.0, 4.5]))

  def test_same_value_scaling(self):
    count = 10
    mmi = SingleMetricMidpointInfo(10 * numpy.ones(count), numpy.full(count, False, dtype=bool))
    assert not mmi.skip
    assert mmi.min == mmi.max == 10
    assert mmi.midpoint == 10
    assert mmi.scale == 1 / 10

    assert mmi.relative_objective_value(2.0) == 0.8
    assert mmi.relative_objective_value(12.0) == -0.2
    assert mmi.relative_objective_variance(0.5) == 0.5 * 0.1**2
    assert mmi.undo_scaling(0.1) == 9.0
    assert mmi.undo_scaling(-3.0) == 40.0
    assert numpy.allclose(mmi.undo_scaling_variances(3.6e-3), 0.36)

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([9.0, 10.0]))

    mmi = SingleMetricMidpointInfo(0.01 * numpy.ones(count), numpy.full(count, False, dtype=bool))
    assert not mmi.skip
    assert mmi.min == mmi.max == 0.01
    assert mmi.midpoint == 0
    assert mmi.scale == 1

    assert mmi.relative_objective_value(0.01) == -0.01
    assert mmi.relative_objective_value(-1.0) == 1.0
    assert mmi.relative_objective_variance(0.5) == 0.5
    assert mmi.undo_scaling(0.1) == -0.1
    assert mmi.undo_scaling(-3.0) == 3.0
    assert mmi.undo_scaling_variances(0.6) == 0.6

    unscaled_values = mmi.undo_scaling(numpy.array([0.01, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([-0.01, 0.0]))

  def test_single_metric_objective_minimize(self):
    metric_objective = "minimize"
    mmi = SingleMetricMidpointInfo(numpy.array([]), numpy.array([], dtype=bool), metric_objective)
    assert mmi.negate == 1
    assert mmi.relative_objective_value(1.0) == 1.0
    assert mmi.relative_objective_value(-10) == -10

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([0.1, 0.0]))

    count = 10
    mmi = SingleMetricMidpointInfo(numpy.arange(count), numpy.full(count, False, dtype=bool), metric_objective)
    assert mmi.relative_objective_value(0.0) == -0.1
    assert mmi.relative_objective_value(9.0) == 0.1
    assert mmi.undo_scaling(0.1) == 9.0
    assert mmi.undo_scaling(-0.1) == 0.0

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([9.0, 4.5]))

  def test_single_metric_objective_maximize(self):
    metric_objective = "maximize"
    mmi = SingleMetricMidpointInfo(numpy.array([]), numpy.array([], dtype=bool), metric_objective)
    assert mmi.negate == -1
    assert mmi.relative_objective_value(1.0) == -1.0
    assert mmi.relative_objective_value(-10) == 10

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([-0.1, 0.0]))

    count = 10
    mmi = SingleMetricMidpointInfo(numpy.arange(count), numpy.full(count, False, dtype=bool), metric_objective)
    assert mmi.relative_objective_value(0.0) == 0.1
    assert mmi.relative_objective_value(9.0) == -0.1
    assert mmi.undo_scaling(0.1) == 0.0
    assert mmi.undo_scaling(-0.1) == 9.0

    unscaled_values = mmi.undo_scaling(numpy.array([0.1, 0.0]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == numpy.array([0.0, 4.5]))

  def test_lie_management(self):
    count = 10
    values = numpy.arange(count)
    failures = numpy.full(count, False, dtype=bool)
    mmi = SingleMetricMidpointInfo(values=values, failures=failures)
    with pytest.raises(AssertionError):
      mmi.compute_lie_value("fake_lie_method")

    mmi = SingleMetricMidpointInfo(values=numpy.array([]), failures=numpy.array([]))
    assert mmi.compute_lie_value(CONSTANT_LIAR_MEAN) == DEFAULT_CONSTANT_LIAR_VALUE

    mmi = SingleMetricMidpointInfo(values=numpy.array([1]), failures=numpy.array([True]))
    assert mmi.compute_lie_value(CONSTANT_LIAR_MAX) == DEFAULT_CONSTANT_LIAR_VALUE

    values = numpy.array([0.1, 0.3, -0.8, -0.2, 0.25])
    failures = numpy.array([False, True, False, True, False], dtype=bool)
    outputs = {
      CONSTANT_LIAR_MIN: -0.8,
      CONSTANT_LIAR_MAX: 0.25,
      CONSTANT_LIAR_MEAN: (0.1 - 0.8 + 0.25) / 3.0,
    }

    mmi = SingleMetricMidpointInfo(values=values, failures=failures)
    for lie_method, lie_value in outputs.items():
      assert mmi.compute_lie_value(lie_method) == lie_value

    failures = numpy.full_like(values, False, dtype=bool)
    outputs = {
      CONSTANT_LIAR_MIN: -0.8,
      CONSTANT_LIAR_MAX: 0.3,
      CONSTANT_LIAR_MEAN: (0.1 + 0.3 - 0.8 - 0.2 + 0.25) / 5.0,
    }

    mmi = SingleMetricMidpointInfo(values=values, failures=failures)
    for lie_method, lie_value in outputs.items():
      assert mmi.compute_lie_value(lie_method) == lie_value

    outputs = {
      CONSTANT_LIAR_MIN: 0.3,
      CONSTANT_LIAR_MAX: -0.8,
      CONSTANT_LIAR_MEAN: (0.1 + 0.3 - 0.8 - 0.2 + 0.25) / 5.0,
    }
    mmi = SingleMetricMidpointInfo(values=values, failures=failures, objective="minimize")
    for lie_method, lie_value in outputs.items():
      assert mmi.compute_lie_value(lie_method) == lie_value


class TestMultiMetricMidpointInfo(NumericalTestCase):
  def test_creation_skip(self):
    with pytest.raises(AssertionError):
      MultiMetricMidpointInfo(numpy.array([]), numpy.array([], dtype=bool))
    with pytest.raises(AssertionError):
      MultiMetricMidpointInfo(numpy.random.random(5), numpy.full(5, True, dtype=bool))

    mmi = MultiMetricMidpointInfo(numpy.random.random((5, 1)), numpy.full(5, True, dtype=bool))
    assert mmi.skip
    assert mmi.relative_objective_value(2.3) == -2.3
    assert mmi.relative_objective_variance(2.3) == 2.3
    assert mmi.relative_objective_variance(0) > 0
    assert mmi.undo_scaling(2.3) == -2.3
    assert mmi.undo_scaling_variances(2.3) == 2.3

    unscaled_values = mmi.undo_scaling(numpy.array([1.3, 5.3]))
    assert isinstance(unscaled_values, numpy.ndarray) and all(unscaled_values == -numpy.array([1.3, 5.3]))

    mmi = MultiMetricMidpointInfo(numpy.random.random((5, 2)), numpy.full(5, True, dtype=bool))
    assert mmi.skip
    assert (mmi.relative_objective_value(numpy.array([2.3, -1])) == numpy.array([-2.3, 1])).all()
    assert (mmi.relative_objective_variance(numpy.array([2.3, 1])) == numpy.array([2.3, 1])).all()
    assert (mmi.relative_objective_variance(numpy.zeros((1, 2))) > numpy.zeros((1, 2))).all()
    assert (mmi.undo_scaling(numpy.array([2.3, 1])) == numpy.array([-2.3, -1])).all()
    assert (mmi.undo_scaling_variances(numpy.array([2.3, 1])) == numpy.array([2.3, 1])).all()

    unscaled_values = mmi.undo_scaling(numpy.array([[1.3, 5.3], [2.1, 2.2]]))
    assert (
      isinstance(unscaled_values, numpy.ndarray) and (unscaled_values == -numpy.array([[1.3, 5.3], [2.1, 2.2]])).all()
    )

  def test_one_metric_all_same(self):
    mmi = MultiMetricMidpointInfo(
      numpy.concatenate((numpy.zeros((5, 1)), numpy.arange(5)[:, None]), axis=1),
      numpy.full(5, False, dtype=bool),
    )
    assert not mmi.skip
    assert (mmi.midpoint == numpy.array([0, 2.0])).all()
    assert (mmi.scale == numpy.array([1, 0.05])).all()

    assert (mmi.relative_objective_value(numpy.array([0.0, 0.0])) == numpy.array([0.0, 0.1])).all()
    assert (mmi.relative_objective_value(numpy.array([9.0, 4.0])) == numpy.array([-9.0, -0.1])).all()
    assert (mmi.relative_objective_variance(0.3) == numpy.array([0.3, (0.2 / 4.0) ** 2 * 0.3])).all()
    assert (mmi.undo_scaling(numpy.array([0.1, 0.1])) == numpy.array([-0.1, 0.0])).all()
    assert (mmi.undo_scaling(numpy.array([-0.1, -0.1])) == numpy.array([0.1, 4.0])).all()
    assert numpy.allclose(mmi.undo_scaling_variances(0.02), [0.02, 8.0], atol=1e-10)

    unscaled_values = mmi.undo_scaling(numpy.array([[0.1, 0.0], [-1.0, 0.1]]))
    assert isinstance(unscaled_values, numpy.ndarray)
    assert (unscaled_values == numpy.array([[-0.1, 2.0], [1.0, 0.0]])).all()

  def test_scaling(self):
    mmi = MultiMetricMidpointInfo(
      numpy.concatenate((numpy.arange(10)[:, None], numpy.arange(0, -10, -1)[:, None]), axis=1),
      numpy.full(10, False, dtype=bool),
    )
    assert not mmi.skip
    assert (mmi.midpoint == numpy.array([4.5, -4.5])).all()
    assert (mmi.scale == 0.2 / 9.0).all()

    assert (mmi.relative_objective_value(numpy.array([0.0, 0.0])) == numpy.array([0.1, -0.1])).all()
    assert (mmi.relative_objective_value(numpy.array([9.0, -9.0])) == numpy.array([-0.1, 0.1])).all()
    assert (mmi.relative_objective_variance(0.3) == (0.2 / 9.0) ** 2 * 0.3).all()
    assert (mmi.undo_scaling(numpy.array([0.1, 0.1])) == numpy.array([0.0, -9.0])).all()
    assert (mmi.undo_scaling(numpy.array([-0.1, -0.1])) == numpy.array([9.0, 0.0])).all()
    assert (mmi.undo_scaling_variances((0.2 / 9.0) ** 2 * 0.3) == 0.3).all()

    unscaled_values = mmi.undo_scaling(numpy.array([[0.1, 0.0], [0.0, 0.1]]))
    assert isinstance(unscaled_values, numpy.ndarray)
    assert (unscaled_values == numpy.array([[0.0, -4.5], [4.5, -9.0]])).all()

  def test_multimetric_objective(self):
    metric_objectives = ["minimize", "maximize"]
    values = numpy.array([[0.0, 0.0], [5.0, 5.0], [10.0, 10.0]])
    mmi = MultiMetricMidpointInfo(values, numpy.full(3, False, dtype=bool), metric_objectives)

    assert mmi.negate.shape[0] == 2
    assert mmi.negate[0] == 1
    assert mmi.negate[1] == -1

    scaled_values = mmi.relative_objective_value(values)
    assert (scaled_values == numpy.array([[-0.1, 0.1], [0.0, 0.0], [0.1, -0.1]])).all()

    unscaled_values = mmi.undo_scaling(scaled_values)
    assert (unscaled_values == numpy.array([[0.0, 0.0], [5.0, 5.0], [10.0, 10.0]])).all()

    assert isinstance(unscaled_values, numpy.ndarray)

  def test_lie_management(self):
    mmi = MultiMetricMidpointInfo(numpy.empty((10, 2)), numpy.full(10, False, dtype=bool))
    with pytest.raises(AssertionError):
      mmi.compute_lie_value("fake_lie_method")

    mmi = MultiMetricMidpointInfo(values=numpy.array([[]]), failures=numpy.array([]))
    assert (mmi.compute_lie_value(CONSTANT_LIAR_MEAN) == DEFAULT_CONSTANT_LIAR_VALUE).all()

    mmi = MultiMetricMidpointInfo(values=numpy.array([[]]), failures=numpy.array([]))
    assert (mmi.compute_lie_value(CONSTANT_LIAR_MIN) == DEFAULT_CONSTANT_LIAR_VALUE).all()

    values = numpy.array([[0.2, 0.5], [0.1, -0.2], [0.7, 0.4], [-0.5, 0.9], [0.8, -0.3]])
    failures = numpy.array([False, True, False, True, False], dtype=bool)
    outputs = {
      CONSTANT_LIAR_MIN: numpy.array([0.2, -0.3]),
      CONSTANT_LIAR_MAX: numpy.array([0.8, 0.5]),
      CONSTANT_LIAR_MEAN: numpy.array([(0.2 + 0.7 + 0.8) / 3, (0.5 + 0.4 - 0.3) / 3]),
    }

    mmi = MultiMetricMidpointInfo(values=values, failures=failures)
    for lie_method, lie_value in outputs.items():
      assert (mmi.compute_lie_value(lie_method) == lie_value).all()
