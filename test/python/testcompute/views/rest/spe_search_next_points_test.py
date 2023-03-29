# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.compute.views.rest.spe_search_next_points import SPESearchNextPoints
from testcompute.zigopt_input_utils import ZigoptSimulator


class TestSearchNextPoints(object):
  def assert_call_successful(self, zigopt_simulator, domain=None):
    if domain:
      view_input = zigopt_simulator.form_spe_search_next_points_input_from_domain(domain)
    else:
      view_input, domain = zigopt_simulator.form_spe_search_next_points_inputs()

    response = SPESearchNextPoints(view_input).call()

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
    num_constraint_metrics,
    num_to_sample,
    num_being_sampled,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=0,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs)

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
      num_tasks=0,
      optimized_metric_thresholds=[0.5] * num_optimized_metrics,
      constraint_metric_thresholds=[0.95] * num_constraint_metrics,
    )
    view_input, _ = zs.form_spe_search_next_points_inputs()
    with pytest.raises(AssertionError):
      SPESearchNextPoints(view_input).call()

  @pytest.mark.parametrize("num_constraint_metrics", [0])
  def test_invalid_num_constraint_metrics(self, num_constraint_metrics):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=15,
      num_optimized_metrics=1,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=25,
      num_being_sampled=5,
      num_tasks=0,
      optimized_metric_thresholds=[0.5],
      constraint_metric_thresholds=[0.95] * num_constraint_metrics,
    )
    view_input, _ = zs.form_spe_search_next_points_inputs()
    with pytest.raises(AssertionError):
      SPESearchNextPoints(view_input).call()
