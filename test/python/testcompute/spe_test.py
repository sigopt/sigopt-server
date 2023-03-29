# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import numpy
import pytest

from libsigopt.compute.covariance import C0RadialMatern, C4RadialMatern
from libsigopt.compute.misc.multimetric import *
from libsigopt.compute.sigopt_parzen_estimator import (
  SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL,
  SigOptParzenEstimator,
  SPEInsufficientDataError,
)
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import form_points_sampled, form_random_unconstrained_categorical_domain


domain = form_random_unconstrained_categorical_domain(numpy.random.randint(4, 12)).one_hot_domain
hparams = [1.0] + (0.2 * numpy.diff(domain.get_lower_upper_bounds(), axis=0)[0]).tolist()
greater_covariance = C4RadialMatern(hparams)
gamma = 0.5


class TestSigoptParzenEstimator(NumericalTestCase):
  @pytest.fixture(scope="class")
  def form_multimetric_info(self):
    def _form_multimetric_info(method_name):
      if method_name == CONVEX_COMBINATION:
        phase = numpy.random.choice([CONVEX_COMBINATION_RANDOM_SPREAD, CONVEX_COMBINATION_SEQUENTIAL])
        phase_kwargs = {"fraction_of_phase_completed": numpy.random.random()}
      elif method_name == EPSILON_CONSTRAINT:
        phase = numpy.random.choice(
          [
            EPSILON_CONSTRAINT_OPTIMIZE_0,
            EPSILON_CONSTRAINT_OPTIMIZE_1,
          ]
        )
        phase_kwargs = {"fraction_of_phase_completed": numpy.random.random()}
      elif method_name == OPTIMIZING_ONE_METRIC:
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

    return _form_multimetric_info

  @pytest.mark.parametrize("phase", [CONVEX_COMBINATION, EPSILON_CONSTRAINT, OPTIMIZING_ONE_METRIC, NOT_MULTIMETRIC])
  def test_form_multimetric_info_fixture(self, form_multimetric_info, phase):
    multimetric_info = form_multimetric_info(phase)
    if phase == NOT_MULTIMETRIC:
      assert multimetric_info.method is None
    else:
      assert multimetric_info.method == phase

  @pytest.mark.parametrize("phase", [CONVEX_COMBINATION, EPSILON_CONSTRAINT, OPTIMIZING_ONE_METRIC, NOT_MULTIMETRIC])
  def test_default(self, form_multimetric_info, phase):
    num_metrics = 1 if phase == NOT_MULTIMETRIC else 2
    points_sampled = form_points_sampled(
      domain=domain,
      num_sampled=numpy.random.randint(100, 200),
      noise_per_point=0,
      num_metrics=num_metrics,
      task_options=numpy.array([]),
      failure_prob=0.1,
    )
    multimetric_info = form_multimetric_info(phase)
    lie_values = numpy.empty(num_metrics)
    points_to_sample = domain.generate_quasi_random_points_in_domain(numpy.random.randint(100, 200))
    points_sampled.points, points_sampled.values = filter_multimetric_points_sampled_spe(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.failures,
      lie_values,
    )

    if len(points_sampled.values) < SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL:
      assert phase == EPSILON_CONSTRAINT
      with pytest.raises(SPEInsufficientDataError):
        SigOptParzenEstimator(
          C0RadialMatern(hparams),
          greater_covariance,
          points_sampled.points,
          points_sampled.values,
          gamma,
        )
      return

    spe = SigOptParzenEstimator(
      C0RadialMatern(hparams),
      greater_covariance,
      points_sampled.points,
      points_sampled.values,
      gamma,
    )
    lpdf, gpdf, ei_vals = spe.evaluate_expected_improvement(points_to_sample)
    assert all(lpdf) > 0 and all(gpdf) > 0 and all(ei_vals) > 0 and len(ei_vals) == len(points_to_sample)
    assert not spe.differentiable
    with pytest.raises(AssertionError):
      spe.evaluate_grad_expected_improvement(points_to_sample)

    spe = SigOptParzenEstimator(
      C4RadialMatern(hparams),
      greater_covariance,
      points_sampled.points,
      points_sampled.values,
      gamma,
    )
    assert spe.differentiable
    ei_grad = spe.evaluate_grad_expected_improvement(points_to_sample)
    assert ei_grad.shape == points_to_sample.shape

  @pytest.mark.parametrize("phase", [CONVEX_COMBINATION, OPTIMIZING_ONE_METRIC, NOT_MULTIMETRIC])
  def test_greater_lower_split(self, form_multimetric_info, phase):
    num_metrics = 1 if phase == NOT_MULTIMETRIC else 2
    points_sampled = form_points_sampled(
      domain=domain,
      num_sampled=numpy.random.randint(100, 200),
      noise_per_point=0,
      num_metrics=num_metrics,
      task_options=numpy.array([]),
      failure_prob=0.1,
    )
    multimetric_info = form_multimetric_info(phase)
    lie_values = numpy.empty(num_metrics)
    points = points_sampled.points
    values = points_sampled.values
    failures = points_sampled.failures
    points, values = filter_multimetric_points_sampled_spe(
      multimetric_info,
      points,
      values,
      failures,
      lie_values,
    )
    # NOTE: max is used here since we don't apply MMI to values when creating SigOptParzenEstimator
    numpy.place(values, failures, numpy.max(values))
    spe = SigOptParzenEstimator(
      C0RadialMatern(hparams),
      greater_covariance,
      points,
      values,
      gamma,
    )
    sorted_indexed = numpy.argsort(values)
    points_sorted = points[sorted_indexed, :]
    lower, greater = points_sorted[: len(points_sorted) // 2], points_sorted[len(points_sorted) // 2 :]
    assert sorted([tuple(l) for l in spe.lower_points]) == sorted([tuple(l) for l in lower])
    assert sorted([tuple(l) for l in spe.greater_points]) == sorted([tuple(l) for l in greater])

  @pytest.mark.parametrize("phase", [CONVEX_COMBINATION, EPSILON_CONSTRAINT, OPTIMIZING_ONE_METRIC, NOT_MULTIMETRIC])
  def test_insufficient_data(self, form_multimetric_info, phase):
    num_metrics = 1 if phase == NOT_MULTIMETRIC else 2
    points_sampled = form_points_sampled(
      domain=domain,
      num_sampled=SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL - 1,
      noise_per_point=0,
      num_metrics=num_metrics,
      task_options=numpy.array([]),
    )
    multimetric_info = form_multimetric_info(phase)
    lie_values = numpy.empty(num_metrics)
    points_sampled.points, points_sampled.values = filter_multimetric_points_sampled_spe(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.failures,
      lie_values,
    )
    with pytest.raises(SPEInsufficientDataError):
      SigOptParzenEstimator(
        C0RadialMatern(hparams),
        greater_covariance,
        points_sampled.points,
        points_sampled.values,
        gamma,
      )

  @pytest.mark.parametrize("phase", [CONVEX_COMBINATION, EPSILON_CONSTRAINT, OPTIMIZING_ONE_METRIC, NOT_MULTIMETRIC])
  def test_insufficient_data_with_forget_factor(self, form_multimetric_info, phase):
    num_metrics = 1 if phase == NOT_MULTIMETRIC else 2
    points_sampled = form_points_sampled(
      domain=domain,
      num_sampled=SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL + 1,
      noise_per_point=0,
      num_metrics=num_metrics,
      task_options=numpy.array([]),
    )
    multimetric_info = form_multimetric_info(phase)
    lie_values = numpy.empty(num_metrics)
    points_sampled.points, points_sampled.values = filter_multimetric_points_sampled_spe(
      multimetric_info,
      points_sampled.points,
      points_sampled.values,
      points_sampled.failures,
      lie_values,
    )
    with pytest.raises(SPEInsufficientDataError):
      SigOptParzenEstimator(
        C0RadialMatern(hparams),
        greater_covariance,
        points_sampled.points,
        points_sampled.values,
        gamma,
        forget_factor=0.5,
      )

  def test_append_and_clear_lies(self):
    num_sampled = numpy.random.randint(100, 200)
    points_sampled_points = domain.generate_quasi_random_points_in_domain(num_sampled)
    points_sampled_values = numpy.random.rand(num_sampled)
    spe = SigOptParzenEstimator(
      C0RadialMatern(hparams),
      greater_covariance,
      points_sampled_points,
      points_sampled_values,
      gamma,
    )
    old_num_lower_points = len(spe.lower_points)
    old_num_greater_points = len(spe.greater_points)
    points_being_sampled_points = domain.generate_quasi_random_points_in_domain(15)
    spe.append_lies(list(points_being_sampled_points))
    assert len(spe.lower_points) == old_num_lower_points
    assert len(spe.greater_points) == old_num_greater_points + 15
    assert numpy.all(spe.greater_lies == points_being_sampled_points)
    assert numpy.all(spe.greater_points[-15:] == points_being_sampled_points)
    assert not spe.lower_lies

    spe.append_lies(list(points_being_sampled_points), lower=True)
    assert len(spe.lower_points) == old_num_lower_points + 15
    assert len(spe.greater_points) == old_num_greater_points + 15
    assert numpy.all(spe.lower_lies == points_being_sampled_points)
    assert numpy.all(spe.lower_points[-15:] == spe.greater_points[-15:])

    spe.clear_lies()
    assert len(spe.lower_points) == old_num_lower_points
    assert len(spe.greater_points) == old_num_greater_points
    assert not spe.lower_lies
    assert not spe.greater_lies

    sorted_indexed = numpy.argsort(points_sampled_values)
    points_sorted = points_sampled_points[sorted_indexed, :]
    lower, greater = points_sorted[: int(len(points_sorted) * gamma)], points_sorted[int(len(points_sorted) * gamma) :]
    assert sorted([tuple(l) for l in spe.lower_points]) == sorted([tuple(l) for l in lower])
    assert sorted([tuple(l) for l in spe.greater_points]) == sorted([tuple(l) for l in greater])
