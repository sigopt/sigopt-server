# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from mock import patch

from libsigopt.aux.constant import PARALLEL_CONSTANT_LIAR
from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE
from libsigopt.compute.views.rest.search_next_points import SearchNextPoints
from testcompute.zigopt_input_utils import ZigoptSimulator


class TestSearchNextPoints(object):
  def assert_call_successful(self, zigopt_simulator, parallelism_method, domain=None):
    if domain:
      view_input = zigopt_simulator.form_search_next_points_view_input_from_domain(domain, parallelism_method)
    else:
      view_input, domain = zigopt_simulator.form_search_next_points_categorical_inputs(parallelism_method)

    response = SearchNextPoints(view_input).call()

    points_to_sample = response["points_to_sample"]
    if len(points_to_sample) != view_input["num_to_sample"]:
      assert domain.is_discrete
      easily_available_points = domain.generate_distinct_random_points(
        view_input["num_to_sample"],
        excluded_points=numpy.array(view_input["points_sampled"].points),
        duplicate_prob=0,
      )
      assert len(points_to_sample) >= len(easily_available_points)
    else:
      assert len(points_to_sample[0]) == view_input["domain_info"].dim
    assert all(domain.check_point_acceptable(p) for p in points_to_sample)

  @pytest.mark.parametrize("dim", [3])
  @pytest.mark.parametrize("num_sampled", [5, 100, 300])
  @pytest.mark.parametrize("num_being_sampled", [0, 5])
  @pytest.mark.parametrize(
    "num_optimized_metrics, optimized_metric_thresholds",
    [
      (0, None),
    ],
  )
  @pytest.mark.parametrize("num_to_sample", [1, 2])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (3, [0.1, 0.67, -0.8]),
    ],
  )
  def test_search_next_points_call(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_to_sample,
    num_being_sampled,
    optimized_metric_thresholds,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  @pytest.mark.parametrize("dim", [3])
  @pytest.mark.parametrize("num_sampled", [5])
  @pytest.mark.parametrize("num_being_sampled", [0, 2])
  @pytest.mark.parametrize(
    "num_optimized_metrics, optimized_metric_thresholds",
    [
      (0, None),
    ],
  )
  @pytest.mark.parametrize("num_to_sample", [1, 5])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (2, [0.67, 0.5]),
      (3, [0.67, 0.5, 0.9]),
    ],
  )
  def test_search_next_points_gp_next_point_ei_failures(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_to_sample,
    num_being_sampled,
    optimized_metric_thresholds,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    parallelism_method = PARALLEL_CONSTANT_LIAR
    view_input, _ = zs.form_search_next_points_categorical_inputs(parallelism_method)

    with patch("libsigopt.compute.views.rest.search_next_points.GpNextPointsCategorical") as mock_gp_next_point:
      search_next_point = SearchNextPoints(view_input)
      search_next_point.search_next_points_expected_improvement_with_failures()

      mock_gp_next_point_args, _ = mock_gp_next_point.call_args

      gp_optimized_metrics_index = mock_gp_next_point_args[0]["metrics_info"].optimized_metrics_index
      gp_constraint_metrics_index = mock_gp_next_point_args[0]["metrics_info"].constraint_metrics_index
      gp_has_constraint_metrics = mock_gp_next_point_args[0]["metrics_info"].has_constraint_metrics
      gp_has_optimization_metrics = mock_gp_next_point_args[0]["metrics_info"].has_optimization_metrics

      assert gp_optimized_metrics_index not in view_input["metrics_info"].optimized_metrics_index
      assert len(gp_optimized_metrics_index) == 1
      assert len(gp_constraint_metrics_index) == num_constraint_metrics - 1
      expected_has_constraint_metrics = num_constraint_metrics > 1
      assert expected_has_constraint_metrics == gp_has_constraint_metrics
      assert gp_has_optimization_metrics
      assert view_input == search_next_point.params

  @pytest.mark.parametrize("dim", [3])
  @pytest.mark.parametrize("num_sampled", [5])
  @pytest.mark.parametrize("num_being_sampled", [0, 5])
  @pytest.mark.parametrize(
    "num_optimized_metrics, optimized_metric_thresholds",
    [
      (0, None),
    ],
  )
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (2, [0.67, 0.5]),
      (3, [0.67, 0.5, 0.9]),
    ],
  )
  def test_search_next_points_gp_next_point_ei(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_to_sample,
    num_being_sampled,
    optimized_metric_thresholds,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    parallelism_method = PARALLEL_CONSTANT_LIAR
    view_input, _ = zs.form_search_next_points_categorical_inputs(parallelism_method)

    with patch("libsigopt.compute.views.rest.search_next_points.GpNextPointsCategorical") as mock_gp_next_point:
      search_next_point = SearchNextPoints(view_input)
      search_next_point.search_next_points_expected_improvement()

      mock_gp_next_point_args, _ = mock_gp_next_point.call_args

      gp_optimized_metrics_index = mock_gp_next_point_args[0]["metrics_info"].optimized_metrics_index
      gp_constraint_metrics_index = mock_gp_next_point_args[0]["metrics_info"].constraint_metrics_index
      gp_has_constraint_metrics = mock_gp_next_point_args[0]["metrics_info"].has_constraint_metrics
      gp_has_optimization_metrics = mock_gp_next_point_args[0]["metrics_info"].has_optimization_metrics

      assert gp_optimized_metrics_index not in view_input["metrics_info"].optimized_metrics_index
      assert len(gp_optimized_metrics_index) == 1
      assert len(gp_constraint_metrics_index) == 0
      assert gp_has_constraint_metrics is False
      assert gp_has_optimization_metrics
      assert view_input == search_next_point.params

  @pytest.mark.parametrize("num_optimized_metrics", [1, 2, 5])
  @pytest.mark.parametrize("num_constraint_metrics", [1, 2])
  def test_invalid_num_optimized_metric(self, num_optimized_metrics, num_constraint_metrics):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=15,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=25,
      num_being_sampled=5,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=[0.5] * num_optimized_metrics,
      constraint_metric_thresholds=[0.95] * num_constraint_metrics,
    )
    parallelism_method = PARALLEL_CONSTANT_LIAR
    view_input, _ = zs.form_search_next_points_categorical_inputs(parallelism_method)
    with pytest.raises(AssertionError):
      SearchNextPoints(view_input).call()

  @pytest.mark.parametrize("num_constraint_metrics", [0])
  def test_invalid_num_constraint_metrics(self, num_constraint_metrics):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=15,
      num_optimized_metrics=1,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=25,
      num_being_sampled=5,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=[0.5],
      constraint_metric_thresholds=[0.95] * num_constraint_metrics,
    )
    parallelism_method = PARALLEL_CONSTANT_LIAR
    view_input, _ = zs.form_search_next_points_categorical_inputs(parallelism_method)
    with pytest.raises(AssertionError):
      SearchNextPoints(view_input).call()
