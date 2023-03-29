# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.aux.adapter_info_containers import MetricsInfo
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  PARALLEL_CONSTANT_LIAR,
  PARALLEL_QEI,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.misc.constant import CONSTANT_LIAR_MIN, NONZERO_MEAN_CONSTANT_MEAN_TYPE
from libsigopt.compute.misc.data_containers import MultiMetricMidpointInfo, SingleMetricMidpointInfo
from libsigopt.compute.views.view import (
  _UNSET,
  GPView,
  View,
  filter_points_sampled,
  form_metric_midpoint_info,
  form_one_hot_points_with_tasks,
  identify_scaled_values_exceeding_scaled_upper_thresholds,
)
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import ZigoptSimulator, form_points_sampled


class TestView(NumericalTestCase):
  mixed_domain = CategoricalDomain(
    [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [3, -1, 5]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 7]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [11, 22]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 6, 9]},
    ]
  )

  metrics_info = MetricsInfo(
    requires_pareto_frontier_optimization=True,
    observation_budget=numpy.random.randint(40, 100),
    user_specified_thresholds=(None, None),
    objectives=["maximize", "minimize"],
    optimized_metrics_index=[0, 1],
    constraint_metrics_index=[],
  )

  def test_filter_points_sampled(self):
    ps = form_points_sampled(
      self.mixed_domain,
      num_sampled=10,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.random.random(2),
      failure_prob=0,
    )
    (
      mps_points,
      mps_values,
      mps_value_vars,
      mps_constraint_values,
      mps_constraint_value_vars,
      mps_failures,
      mps_task_costs,
    ) = filter_points_sampled(ps, self.metrics_info)
    assert (mps_points == ps.points).all()
    assert (mps_values == ps.values).all()
    assert (mps_value_vars == ps.value_vars).all()
    assert (mps_failures == ps.failures).all()
    assert (mps_task_costs == ps.task_costs).all()
    assert mps_constraint_values is _UNSET
    assert mps_constraint_value_vars is _UNSET

  def test_form_metric_midpoint_info(self):
    ps = form_points_sampled(
      self.mixed_domain,
      num_sampled=10,
      noise_per_point=1e-5,
      num_metrics=1,
      task_options=numpy.random.random(2),
      failure_prob=0.5,
    )
    mmi = form_metric_midpoint_info(ps.values, ps.failures, ["maximize"])
    assert isinstance(mmi, MultiMetricMidpointInfo)

    ps.values = ps.values[:, 0]
    mmi = form_metric_midpoint_info(ps.values, ps.failures, ["maximize"])
    assert isinstance(mmi, SingleMetricMidpointInfo)

    ps = form_points_sampled(
      self.mixed_domain,
      num_sampled=10,
      noise_per_point=1e-5,
      num_metrics=2,
      task_options=numpy.random.random(2),
      failure_prob=0.5,
    )
    mmi = form_metric_midpoint_info(ps.values, ps.failures, ["maximize", "minimize"])
    assert isinstance(mmi, MultiMetricMidpointInfo)

  def test_form_one_hot_points_with_tasks(self):
    ps = form_points_sampled(
      self.mixed_domain,
      num_sampled=10,
      noise_per_point=1e-5,
      num_metrics=1,
      task_options=numpy.random.random(2),
      failure_prob=0.5,
    )
    with pytest.raises(AssertionError):
      form_one_hot_points_with_tasks(
        self.mixed_domain.one_hot_domain,
        ps.points,
        ps.task_costs,
      )

    one_hot_points_with_no_task_costs = form_one_hot_points_with_tasks(
      self.mixed_domain,
      ps.points,
      None,
    )
    one_hot_points_with_task_costs = form_one_hot_points_with_tasks(
      self.mixed_domain,
      ps.points,
      ps.task_costs,
    )
    assert (one_hot_points_with_no_task_costs == one_hot_points_with_task_costs[:, :-1]).all()
    assert (ps.task_costs == one_hot_points_with_task_costs[:, -1]).all()

  # pylint: disable=pointless-statement
  def check_gp_ei_fields(self, zigopt_simulator):
    view_input = zigopt_simulator.form_gp_ei_categorical_inputs(CONSTANT_LIAR_MIN)
    v = GPView(view_input)
    assert v.has_optimization_metrics
    assert v.polynomial_indices is not object()
    assert v.one_hot_points_being_sampled_points is not object()
    assert v.one_hot_points_to_evaluate_points is not object()

  def check_gp_hyper_opt_fields(self, zigopt_simulator):
    view_input, _ = zigopt_simulator.form_gp_hyper_opt_categorical_inputs()
    v = GPView(view_input)
    assert v.polynomial_indices is not object()
    assert v.has_optimization_metrics
    with pytest.raises(KeyError):
      v.one_hot_points_being_sampled_points
    with pytest.raises(KeyError):
      v.one_hot_points_to_evaluate_points

  def check_gp_next_points_fields(self, zigopt_simulator, parallelism_method):
    view_input, _ = zigopt_simulator.form_gp_next_points_categorical_inputs(parallelism_method)
    v = GPView(view_input)
    assert v.has_optimization_metrics
    assert v.polynomial_indices is not object()
    assert v.one_hot_points_being_sampled_points is not object()
    with pytest.raises(KeyError):
      v.one_hot_points_to_evaluate_points

  # pylint: enable=pointless-statement

  @pytest.mark.parametrize("dim", [3, 7])
  @pytest.mark.parametrize("num_sampled", [19, 41])
  @pytest.mark.parametrize("num_being_sampled", [5])
  @pytest.mark.parametrize("num_to_sample", [26])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  @pytest.mark.parametrize("num_tasks", [0, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (0, None),
      (2, numpy.random.random(2)),
    ],
  )
  @pytest.mark.parametrize("num_stored_metrics", [0, 1])
  def test_gp_views_fields_base(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
    num_being_sampled,
    num_to_sample,
    nonzero_mean_type,
    use_tikhonov,
    num_tasks,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_being_sampled=num_being_sampled,
      num_to_sample=num_to_sample,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=num_tasks,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.check_gp_ei_fields(zs)
    self.check_gp_hyper_opt_fields(zs)

    for parallelism_method in (PARALLEL_QEI, PARALLEL_CONSTANT_LIAR):
      self.check_gp_next_points_fields(zs, parallelism_method)

  @pytest.mark.parametrize("dim", [3, 7, 56])
  @pytest.mark.parametrize("num_optimized_metrics", [2])
  @pytest.mark.parametrize("num_stored_metrics", [0, 3])
  @pytest.mark.parametrize("num_sampled", [36, 107, 960])
  def test_identify_values_exceeding_user_specified_thresholds(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_stored_metrics,
  ):
    zs = ZigoptSimulator(dim, num_sampled, num_optimized_metrics, num_stored_metrics, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].optimized_metrics_index = [0, 1]
    values = view_input["points_sampled"].values
    metric_0_lower_bound = numpy.random.uniform(min(values[:, 0]), max(values[:, 0]))
    metric_1_lower_bound = numpy.random.uniform(min(values[:, 1]), max(values[:, 1]))

    num_metrics = num_optimized_metrics + num_stored_metrics
    user_specified_thresholds = [None for _ in range(num_metrics)]
    user_specified_thresholds[0] = metric_0_lower_bound
    user_specified_thresholds[1] = metric_1_lower_bound
    view_input["metrics_info"].user_specified_thresholds = user_specified_thresholds

    view = View(view_input)
    told_to_exclude = identify_scaled_values_exceeding_scaled_upper_thresholds(
      view.points_sampled_for_af_values,
      view.optimized_metrics_thresholds,
    )
    bounds_array = numpy.array([[metric_0_lower_bound, metric_1_lower_bound]])
    should_exclude = numpy.logical_not(
      numpy.prod(
        values[:, view.optimized_metrics_index] > bounds_array,
        axis=1,
        dtype=bool,
      )
    )
    assert numpy.array_equal(told_to_exclude, should_exclude)

  @pytest.mark.parametrize("dim", [3, 7])
  @pytest.mark.parametrize("num_sampled", [19, 41])
  @pytest.mark.parametrize("num_being_sampled", [0, 1, 5])
  @pytest.mark.parametrize("num_to_sample", [26])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  @pytest.mark.parametrize("num_tasks", [0, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [0])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, numpy.random.random(1)),
      (4, numpy.random.random(4)),
    ],
  )
  @pytest.mark.parametrize("num_stored_metrics", [0, 1])
  @pytest.mark.parametrize("parallelism_method", [PARALLEL_QEI, PARALLEL_CONSTANT_LIAR])
  def test_view_search_no_optimization(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
    num_being_sampled,
    num_to_sample,
    nonzero_mean_type,
    use_tikhonov,
    num_tasks,
    constraint_metric_thresholds,
    parallelism_method,
  ):
    zigopt_simulator = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_being_sampled=num_being_sampled,
      num_to_sample=num_to_sample,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=num_tasks,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    view_input, _ = zigopt_simulator.form_search_next_points_categorical_inputs(parallelism_method)
    view = View(view_input)
    assert not view.has_optimization_metrics
    assert view.optimized_metrics_objectives is _UNSET
    assert view.optimized_metrics_index is _UNSET
    assert view.optimized_metrics_thresholds is _UNSET
    assert view.points_sampled_for_af_values is _UNSET
    assert view.points_sampled_for_af_value_vars is _UNSET

  @pytest.mark.parametrize("dim", [7])
  @pytest.mark.parametrize("num_sampled", [27])
  @pytest.mark.parametrize("num_being_sampled", [0, 5])
  @pytest.mark.parametrize("num_to_sample", [26])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  @pytest.mark.parametrize("num_tasks", [0, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [0])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (0, None),
    ],
  )
  @pytest.mark.parametrize("num_stored_metrics", [0, 1])
  @pytest.mark.parametrize("parallelism_method", [PARALLEL_QEI, PARALLEL_CONSTANT_LIAR])
  def test_view_search_no_optimization_no_constraint_metric(
    self,
    dim,
    num_sampled,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
    num_being_sampled,
    num_to_sample,
    nonzero_mean_type,
    use_tikhonov,
    num_tasks,
    constraint_metric_thresholds,
    parallelism_method,
  ):
    zigopt_simulator = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_being_sampled=num_being_sampled,
      num_to_sample=num_to_sample,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=num_tasks,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    view_input, _ = zigopt_simulator.form_search_next_points_categorical_inputs(parallelism_method)
    with pytest.raises(AssertionError):
      View(view_input)
