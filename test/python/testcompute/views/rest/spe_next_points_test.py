# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from flaky import flaky

from libsigopt.aux.adapter_info_containers import MetricsInfo
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.misc.constant import MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
from libsigopt.compute.views.rest.spe_next_points import (
  COMPLETION_PHASE,
  INITIALIZATION_PHASE,
  SKO_PHASE,
  SPE_PHANTOM_BUDGET_FACTOR,
  SPENextPoints,
  get_experiment_phase,
)
from testcompute.domain_test import samples_satisfy_kolmogorov_smirnov_test
from testcompute.zigopt_input_utils import ZigoptSimulator


PHASE_LIST = [
  (1, 0, INITIALIZATION_PHASE),
  (10, 0, INITIALIZATION_PHASE),
  (10, 10, INITIALIZATION_PHASE),
  (20, 0, SKO_PHASE),
  (20, 10, INITIALIZATION_PHASE),
  (20, 20, INITIALIZATION_PHASE),
  (50, 0, SKO_PHASE),
  (50, 45, SKO_PHASE),
  (50, 46, INITIALIZATION_PHASE),
  (50, 50, INITIALIZATION_PHASE),
  (75, 0, COMPLETION_PHASE),
  (75, 1, SKO_PHASE),
  (99, 9, COMPLETION_PHASE),
  (99, 25, SKO_PHASE),
  (99, 92, INITIALIZATION_PHASE),
]


class TestSPENextPointsViews(object):
  def assert_call_successful(self, zigopt_simulator, domain=None):
    if domain:
      view_input = zigopt_simulator.form_spe_next_points_view_input_from_domain(domain)
    else:
      view_input, domain = zigopt_simulator.form_spe_next_points_inputs()

    response = SPENextPoints(view_input).call()

    points_to_sample = response["points_to_sample"]
    assert len(points_to_sample) == view_input["num_to_sample"]
    assert len(points_to_sample[0]) == view_input["domain_info"].dim
    assert all(domain.check_point_acceptable(p) for p in points_to_sample)

    task_options = numpy.array(view_input["task_options"])
    if task_options.size:
      task_costs = response["task_costs"]
      assert len(task_costs) == len(points_to_sample)
      assert all(tc in task_options for tc in task_costs)
    else:
      assert "task_costs" not in response

  @pytest.mark.parametrize("dim", [6, 38])
  @pytest.mark.parametrize("num_sampled", [19, 40, 151])
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 9, 81])
  def test_spe_base(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
    )
    self.assert_call_successful(zs)

  @pytest.mark.parametrize("dim", [6, 38])
  @pytest.mark.parametrize("num_sampled", [19, 40, 151])
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 9, 81])
  def test_spe_multitask(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=3,
    )
    self.assert_call_successful(zs)

  @pytest.mark.parametrize("num_sampled", [23, 433])
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 44])
  def test_spe_constraints(
    self,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
  ):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 1]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 3, 5]},
    ]
    constraint_list = [
      {"weights": [1, 1, 0, 0, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      {"weights": [1, 1, 1, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list)
    zs = ZigoptSimulator(
      dim=domain.dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
    )
    self.assert_call_successful(zs, domain=domain)

  def test_identify_spe_failures(self):
    zs = ZigoptSimulator(3, 22, 1, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["points_sampled"].failures[0] = True
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert augmented_points_sampled_failures[0]
    assert not numpy.any(augmented_points_sampled_failures[1:])

    zs = ZigoptSimulator(3, 22, 2, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].user_specified_thresholds = (
      None,
      None,
    )
    view_input["points_sampled"].failures[-1] = True
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert augmented_points_sampled_failures[-1]
    assert not numpy.any(augmented_points_sampled_failures[:-1])

  @pytest.mark.parametrize("dim", [3, 7, 56])
  @pytest.mark.parametrize("num_sampled", [106, 507, 960])
  def test_identify_spe_failures_with_bounds_violations(self, dim, num_sampled):
    zs = ZigoptSimulator(dim, num_sampled, 2, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].user_specified_thresholds = (
      None,
      None,
    )
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert numpy.all(numpy.logical_not(augmented_points_sampled_failures))

    # Choose a situation with points on both sides of the metric bound (with high probability)
    values = view_input["points_sampled"].values
    metric_1_lower_bound = metric_0_lower_bound = 0
    view_input["metrics_info"].user_specified_thresholds = [
      metric_0_lower_bound,
      metric_1_lower_bound,
    ]
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    bounds_array = numpy.array([[metric_0_lower_bound, metric_1_lower_bound]])
    should_exclude = numpy.logical_not(numpy.prod(values > bounds_array, axis=1, dtype=bool))
    assert numpy.array_equal(augmented_points_sampled_failures, should_exclude)

    # Confirm this works with only one bound attached
    values = view_input["points_sampled"].values
    metric_0_lower_bound = 0
    view_input["metrics_info"].user_specified_thresholds = (
      metric_0_lower_bound,
      None,
    )
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    bounds_array = numpy.array([[metric_0_lower_bound, -numpy.inf]])
    should_exclude = numpy.logical_not(numpy.prod(values > bounds_array, axis=1, dtype=bool))
    assert numpy.array_equal(augmented_points_sampled_failures, should_exclude)

    # Confirm this works with a small number of failures present in the data naturally
    zs = ZigoptSimulator(dim, num_sampled, 2, failure_prob=0.2)
    view_input, _ = zs.form_spe_next_points_inputs()
    values = view_input["points_sampled"].values
    metric_1_lower_bound = metric_0_lower_bound = 0
    view_input["metrics_info"].user_specified_thresholds = [
      metric_0_lower_bound,
      metric_1_lower_bound,
    ]
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    bounds_array = numpy.array([[metric_0_lower_bound, metric_1_lower_bound]])
    should_exclude = numpy.logical_not(numpy.prod(values > bounds_array, axis=1, dtype=bool))
    natural_failures = view.points_sampled_failures
    assert numpy.array_equal(augmented_points_sampled_failures, numpy.logical_or(should_exclude, natural_failures))

  @pytest.mark.parametrize("dim", [3, 56])
  def test_identify_spe_failures_with_metric_constraints(self, dim):
    zs = ZigoptSimulator(dim, 603, 2, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()

    # Confirm this works with only one bound attached
    values = view_input["points_sampled"].values
    metric_0_lower_bound = 0
    view_input["metrics_info"] = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      user_specified_thresholds=[metric_0_lower_bound, None],
      objectives=["maximize", "maximize"],
      optimized_metrics_index=[1],
      constraint_metrics_index=[0],
      observation_budget=10,
    )
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    bounds_array = numpy.array([[metric_0_lower_bound, -numpy.inf]])
    should_exclude = numpy.logical_not(numpy.prod(values > bounds_array, axis=1, dtype=bool))
    assert numpy.array_equal(augmented_points_sampled_failures, should_exclude)

    view_input["points_sampled"].failures[:270] = True
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    bounds_array = numpy.array([[metric_0_lower_bound, -numpy.inf]])
    should_exclude = numpy.logical_not(numpy.prod(values > bounds_array, axis=1, dtype=bool))
    assert numpy.all(augmented_points_sampled_failures[:270])
    assert numpy.array_equal(augmented_points_sampled_failures[270:], should_exclude[270:])

  def test_identify_spe_failures_with_bounds_violations_edge_cases(self):
    # Consider when none of the points satisfy the stated bounds (ignore the bounds, only deal with normal failures)
    n = 15
    zs = ZigoptSimulator(5, n, 2, failure_prob=0)
    view_input, _ = zs.form_spe_next_points_inputs()
    metric_1_lower_bound = metric_0_lower_bound = 0
    view_input["metrics_info"].user_specified_thresholds = [
      metric_0_lower_bound,
      metric_1_lower_bound,
    ]
    view_input["points_sampled"].values = numpy.full((n, 2), -1)
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert not numpy.any(augmented_points_sampled_failures)

    # Consider when there are already too many failures present to allow the bounds
    num_natural_fails = n - MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS + 1
    view_input["points_sampled"].values = numpy.concatenate(
      (numpy.random.random((n - num_natural_fails, 2)) - 1, numpy.random.random((num_natural_fails, 2))),
      axis=0,
    )
    expected_bounds_violations = numpy.concatenate((numpy.ones(n - num_natural_fails), numpy.zeros(num_natural_fails)))
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert numpy.array_equiv(augmented_points_sampled_failures, expected_bounds_violations)

    view_input["points_sampled"].failures[:num_natural_fails] = True
    view = SPENextPoints(view_input)
    augmented_points_sampled_failures = view.augment_failures_with_user_specified_thresholds_violations()
    assert numpy.array_equal(augmented_points_sampled_failures, view_input["points_sampled"].failures)

  # These optimized_metric_thresholds could maybe be more intelligent in tests where function values are complicated
  @pytest.mark.parametrize("dim", [23])
  @pytest.mark.parametrize("num_sampled", [19, 40, 151])
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize("num_being_sampled", [0, 44])
  @pytest.mark.parametrize("optimized_metric_thresholds", [[None, None], [None, -0.01234], [0, None], [0.1234, 0.0567]])
  def test_spe_optimized_metric_thresholds(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_being_sampled,
    optimized_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=2,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
    )
    self.assert_call_successful(zs)

  # These optimized_metric_thresholds could maybe be more intelligent in tests where function values are complicated
  @pytest.mark.parametrize("dim", [7])
  @pytest.mark.parametrize(
    "optimized_metric_thresholds", [[None, None], [None, -0.01234], [0, None], [0.1234, 0.05678]]
  )
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, numpy.random.random(1)),
      (3, numpy.random.random(3)),
    ],
  )
  @pytest.mark.parametrize("num_stored_metrics", [0, 8])
  def test_spe_optimized_metric_constraints(
    self,
    dim,
    num_constraint_metrics,
    num_stored_metrics,
    optimized_metric_thresholds,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=433,
      num_optimized_metrics=2,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_to_sample=10,
      num_being_sampled=7,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs)

  @pytest.mark.parametrize("dim", [9])
  @pytest.mark.parametrize("num_sampled", [23, 433])
  @pytest.mark.parametrize("num_to_sample", [1, 3])
  @pytest.mark.parametrize("num_being_sampled", [0, 44])
  def test_spe_no_optimized_metrics(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_being_sampled,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=0,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
    )
    with pytest.raises(AssertionError):
      self.assert_call_successful(zs)

  @pytest.mark.parametrize("dim", [4])
  @pytest.mark.parametrize("observation_count, failure_count, phase", PHASE_LIST)
  def test_spe_phases(self, dim, observation_count, failure_count, phase):
    observation_budget = 100

    # Check computed phase
    computed_phase, _ = get_experiment_phase(
      budget=observation_budget,
      observation_count=observation_count,
      failure_count=failure_count,
    )
    assert computed_phase == phase

    # Create view_input with desired observation_budget, observation_count, and failure_count
    failures = numpy.array([False] * observation_count)
    failures[:failure_count] = True
    zs = ZigoptSimulator(dim=dim, num_sampled=observation_count)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].observation_budget = observation_budget
    view_input["points_sampled"].failures = failures

    # Check phase in views
    response = SPENextPoints(view_input).call()
    assert response["tag"]["spe_phase"] == phase

  @pytest.mark.parametrize("dim", [2])
  @pytest.mark.parametrize("observation_count, failure_count, phase", PHASE_LIST)
  def test_spe_phases_no_observation_budget(self, dim, observation_count, failure_count, phase):
    # Check computed phase
    computed_phase, _ = get_experiment_phase(
      budget=dim * SPE_PHANTOM_BUDGET_FACTOR,
      observation_count=observation_count,
      failure_count=failure_count,
    )
    assert computed_phase == phase

    # Create view_input with desired observation_budget, observation_count, and failure_count
    failures = numpy.array([False] * observation_count)
    failures[:failure_count] = True
    zs = ZigoptSimulator(dim=dim, num_sampled=observation_count)
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].observation_budget = None
    view_input["points_sampled"].failures = failures

    # Check phase in views
    response = SPENextPoints(view_input).call()
    assert response["tag"]["spe_phase"] == phase

  @pytest.mark.parametrize("num_sampled", [23, 433])
  @pytest.mark.parametrize("num_to_sample", [1, 10])
  @pytest.mark.parametrize("num_being_sampled", [0, 44])
  def test_spe_no_observation_budget(
    self,
    num_sampled,
    num_to_sample,
    num_being_sampled,
  ):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=num_sampled,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      num_tasks=0,
    )
    view_input, _ = zs.form_spe_next_points_inputs()
    view_input["metrics_info"].observation_budget = None
    view = SPENextPoints(view_input)
    response = view.call()
    points_to_sample = response["points_to_sample"]
    assert len(points_to_sample) == view_input["num_to_sample"]
    assert len(points_to_sample[0]) == view_input["domain_info"].dim

  @flaky(max_runs=2)
  def test_spe_with_priors_initialization_phase(self):  # Check that priors are used in spe_next_points initialization
    n_samples = 500
    zs = ZigoptSimulator(dim=2, num_sampled=10, num_to_sample=n_samples)
    peaky_normal_prior = {"name": ParameterPriorNames.NORMAL, "params": {"mean": -100, "scale": 0.001}}
    heavy_tailed_beta_prior = {"name": ParameterPriorNames.BETA, "params": {"shape_a": 2, "shape_b": 50}}
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-200, 0]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
      ],
      priors=[
        peaky_normal_prior,
        heavy_tailed_beta_prior,
      ],
    )
    view_input = zs.form_spe_next_points_view_input_from_domain(domain)
    view_input["metrics_info"].observation_budget = 1000
    view = SPENextPoints(view_input)
    response = view.call()
    prior_samples = response["points_to_sample"]

    assert samples_satisfy_kolmogorov_smirnov_test(
      prior_samples[:, 0],
      domain.domain_components[0],
      peaky_normal_prior,
    )
    assert samples_satisfy_kolmogorov_smirnov_test(
      prior_samples[:, 1],
      domain.domain_components[1],
      heavy_tailed_beta_prior,
    )
