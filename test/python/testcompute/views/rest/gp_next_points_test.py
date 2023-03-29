# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from flaky import flaky
from mock import Mock

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  PARALLEL_CONSTANT_LIAR,
  PARALLEL_QEI,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.multitask_acquisition_function import MultitaskAcquisitionFunction
from libsigopt.compute.views.rest.gp_next_points_categorical import (
  GpNextPointsCategorical,
  convert_from_one_hot,
  find_best_one_hot_neighbor_by_af,
  form_augmented_domain,
  generate_neighboring_categorical_points,
  generate_neighboring_integer_points,
  get_discrete_conversion_option,
)
from testaux.numerical_test_case import NumericalTestCase
from testcompute.domain_test import domains_approximately_equal
from testcompute.zigopt_input_utils import ZigoptSimulator, form_random_unconstrained_categorical_domain


class TestCategoricalNextPoints(NumericalTestCase):
  mixed_domain = CategoricalDomain(
    [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [3, -1, 5]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 7]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [11, 22]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 6, 9]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.1, 0.2, 0.5, 9.0]},
    ]
  )

  def assert_call_successful(self, zigopt_simulator, parallelism_method, domain=None):
    if domain:
      view_input = zigopt_simulator.form_gp_next_points_view_input_from_domain(domain, parallelism_method)
    else:
      view_input, domain = zigopt_simulator.form_gp_next_points_categorical_inputs(parallelism_method)
    response = GpNextPointsCategorical(view_input).call()

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

    task_options = numpy.array(view_input["task_options"])
    if task_options.size:
      task_costs = response["task_costs"]
      assert len(task_costs) == len(points_to_sample)
      assert all(tc in task_options for tc in task_costs)
    else:
      assert "task_costs" not in response

  @pytest.mark.parametrize("dim", [4])
  @pytest.mark.parametrize("num_sampled", [27])
  @pytest.mark.parametrize("num_to_sample", [2])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 3])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [False])
  def test_constant_liar_base(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=0,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  @pytest.mark.parametrize("dim", [3])
  @pytest.mark.parametrize("num_sampled", [39])
  @pytest.mark.parametrize("num_to_sample", [2])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [4])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True])
  def test_constant_liar_multitask(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=3,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  # TODO(RTL-94): Increase num_to_sample after I think about what to do about QEI int snapping
  def test_qei_base(self):
    domain = form_random_unconstrained_categorical_domain(4, categoricals_allowed=False)
    zs = ZigoptSimulator(
      dim=domain.dim,
      num_sampled=40,
      num_optimized_metrics=1,
      num_to_sample=1,
      num_being_sampled=4,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      use_tikhonov=False,
      num_tasks=0,
    )
    self.assert_call_successful(zs, PARALLEL_QEI, domain=domain)

  @pytest.mark.parametrize("num_sampled", [52])
  @pytest.mark.parametrize("num_to_sample", [2])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [3])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [False])
  @pytest.mark.parametrize("num_tasks", [0, 2])
  def test_constant_liar_constraints(
    self,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
    num_tasks,
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
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=num_tasks,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR, domain=domain)

  @pytest.mark.parametrize("dim", [4])
  @pytest.mark.parametrize("num_sampled", [32])
  @pytest.mark.parametrize("num_to_sample", [2])
  @pytest.mark.parametrize("num_being_sampled", [1])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [False])
  @pytest.mark.parametrize("optimized_metric_thresholds", [[None, None], [None, -0.01234], [0.1234, 0.05678]])
  def test_constant_liar_metric_thresholds(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
    optimized_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=2,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  @pytest.mark.parametrize(
    "num_optimized_metrics, optimized_metric_thresholds",
    [
      (1, None),
      (2, [None, 0.2]),
      (2, [0.13, -0.5]),
    ],
  )
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (2, [0.67, -0.8]),
    ],
  )
  def test_constant_liar_metric_constraints(
    self,
    num_optimized_metrics,
    num_constraint_metrics,
    optimized_metric_thresholds,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=35,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=2,
      num_being_sampled=2,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      optimized_metric_thresholds=optimized_metric_thresholds,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (2, [0.67, -0.8]),
    ],
  )
  def test_qei_metric_constraints(
    self,
    num_constraint_metrics,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=35,
      num_optimized_metrics=1,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=1,
      num_being_sampled=2,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_QEI)

  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (1, [0.67]),
      (2, [0.67, -0.8]),
    ],
  )
  @pytest.mark.parametrize("parallelism_method", [PARALLEL_CONSTANT_LIAR, PARALLEL_QEI])
  def test_no_optimized_metrics(
    self,
    num_constraint_metrics,
    constraint_metric_thresholds,
    parallelism_method,
  ):
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=35,
      num_optimized_metrics=0,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=2,
      num_being_sampled=2,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      num_tasks=0,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    with pytest.raises(AssertionError):
      self.assert_call_successful(zs, parallelism_method)


class TestDiscreteNextPointsConversion(NumericalTestCase):
  mixed_domain = CategoricalDomain(
    [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [3, -1, 5]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 7]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [11, 22]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 6, 9]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.1, 0.2, 0.5, 9.0]},
    ]
  )

  def test_neighboring_integer_recognition(self):
    one_hot_point = [0.4, 0.5, 0.6, 2.3, -0.5, 17.2, -5.2, 0.1, 0.9, 0.5, 0.3, 2.3]
    assert self.mixed_domain.one_hot_domain.check_point_acceptable(one_hot_point)
    neighboring_integer_points = generate_neighboring_integer_points(one_hot_point, self.mixed_domain)
    known_neighbors = numpy.array(
      [
        [0.4, 0.5, 0.6, 2.0, -0.5, 17.0, -5.2, 0.1, 0.9, 0.5, 0.3, 2.3],
        [0.4, 0.5, 0.6, 2.0, -0.5, 18.0, -5.2, 0.1, 0.9, 0.5, 0.3, 2.3],
        [0.4, 0.5, 0.6, 3.0, -0.5, 17.0, -5.2, 0.1, 0.9, 0.5, 0.3, 2.3],
        [0.4, 0.5, 0.6, 3.0, -0.5, 18.0, -5.2, 0.1, 0.9, 0.5, 0.3, 2.3],
      ]
    )
    self.assert_vector_within_relative(neighboring_integer_points, known_neighbors, 0)
    assert all(self.mixed_domain.one_hot_domain.check_point_acceptable(p) for p in neighboring_integer_points)

  def test_neighboring_categories_recognition(self):
    one_hot_point = [0.4, 0.5, 0.6, 2.3, -0.5, 17.2, -5.2, 0.1, 0.9, 0.5, 0.3, 0.5]
    assert self.mixed_domain.one_hot_domain.check_point_acceptable(one_hot_point)
    neighboring_categorical_points = generate_neighboring_categorical_points(
      numpy.atleast_2d(one_hot_point),
      self.mixed_domain,
    )
    known_neighbors = numpy.array(
      [
        [1.0, 0.0, 0.0, 2.3, -0.5, 17.2, -5.2, 1.0, 0.0, 0.0, 0.0, 0.5],
        [1.0, 0.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 1.0, 0.0, 0.0, 0.5],
        [1.0, 0.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 1.0, 0.0, 0.5],
        [1.0, 0.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 0.0, 1.0, 0.5],
        [0.0, 1.0, 0.0, 2.3, -0.5, 17.2, -5.2, 1.0, 0.0, 0.0, 0.0, 0.5],
        [0.0, 1.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 1.0, 0.0, 0.0, 0.5],
        [0.0, 1.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 1.0, 0.0, 0.5],
        [0.0, 1.0, 0.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 0.0, 1.0, 0.5],
        [0.0, 0.0, 1.0, 2.3, -0.5, 17.2, -5.2, 1.0, 0.0, 0.0, 0.0, 0.5],
        [0.0, 0.0, 1.0, 2.3, -0.5, 17.2, -5.2, 0.0, 1.0, 0.0, 0.0, 0.5],
        [0.0, 0.0, 1.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 1.0, 0.0, 0.5],
        [0.0, 0.0, 1.0, 2.3, -0.5, 17.2, -5.2, 0.0, 0.0, 0.0, 1.0, 0.5],
      ]
    )
    self.assert_vector_within_relative(neighboring_categorical_points, known_neighbors, 0)
    assert all(self.mixed_domain.one_hot_domain.check_point_acceptable(p) for p in neighboring_categorical_points)

  def test_discrete_conversion_option(self):
    continuous_component = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
    ]
    int_component = [
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
    ]
    cat_component = [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 3, 5]},
    ]

    continuous_only_domain = CategoricalDomain(continuous_component * 5)
    option = get_discrete_conversion_option(continuous_only_domain)
    assert option == "none"

    continuous_and_small_int_domain = CategoricalDomain(continuous_component * 5 + int_component * 3)
    option = get_discrete_conversion_option(continuous_and_small_int_domain)
    assert option == INT_EXPERIMENT_PARAMETER_NAME

    continuous_and_big_int_domain = CategoricalDomain(continuous_component * 5 + int_component * 20)
    option = get_discrete_conversion_option(continuous_and_big_int_domain)
    assert option == "none"

    continuous_and_small_cat_domain = CategoricalDomain(continuous_component * 5 + cat_component * 3)
    option = get_discrete_conversion_option(continuous_and_small_cat_domain)
    assert option == "cat"

    continuous_and_big_cat_domain = CategoricalDomain(continuous_component * 5 + cat_component * 8)
    option = get_discrete_conversion_option(continuous_and_big_cat_domain)
    assert option == "none"

    big_int_small_cat_domain = CategoricalDomain(int_component * 20 + cat_component * 3)
    option = get_discrete_conversion_option(big_int_small_cat_domain)
    assert option == "cat"

    small_int_big_cat_domain = CategoricalDomain(int_component * 5 + cat_component * 8)
    option = get_discrete_conversion_option(small_int_big_cat_domain)
    assert option == INT_EXPERIMENT_PARAMETER_NAME

    big_int_big_cat_domain = CategoricalDomain(int_component * 20 + cat_component * 8)
    option = get_discrete_conversion_option(big_int_big_cat_domain)
    assert option == "none"

    small_int_small_cat_domain = CategoricalDomain(int_component * 2 + cat_component * 2)
    option = get_discrete_conversion_option(small_int_small_cat_domain)
    assert option == "both"

    small_int_small_cat_big_product_domain = CategoricalDomain(int_component * 13 + cat_component * 6)
    option = get_discrete_conversion_option(small_int_small_cat_big_product_domain)
    assert option == INT_EXPERIMENT_PARAMETER_NAME

  @flaky(max_runs=2)
  def test_convert_from_one_hot(self):
    class dummy_acquisition_function(object):
      def evaluate_at_point_list(self, x):
        return numpy.arange(len(x))

    one_hot_points = numpy.array(
      [
        [0.4, 0.5, 0.6, 2.8, -0.5, 17.2, -5.2, 0.1, 0.9, 0.5, 0.3, 0.23],
        [0.9, 0.2, 0.6, 4.3, -0.1, 19.5, 2.2, 0.8, 0.2, 0.9, 0.4, -2.0],
      ]
    )
    none_best_one_hot_points = find_best_one_hot_neighbor_by_af(
      one_hot_points,
      self.mixed_domain,
      dummy_acquisition_function(),
      "none",
    )
    assert numpy.all(one_hot_points == none_best_one_hot_points)

    int_best_one_hot_neighbors = find_best_one_hot_neighbor_by_af(
      one_hot_points,
      self.mixed_domain,
      dummy_acquisition_function(),
      INT_EXPERIMENT_PARAMETER_NAME,
    )
    correct_answers_int_best_one_hot_neighbors = numpy.array(
      [
        [0.0, 0.0, 1.0, 3.0, -0.5, 18.0, -5.2, 0.0, 1.0, 0.0, 0.0, 0.2],
        [1.0, 0.0, 0.0, 5.0, -0.1, 20.0, 2.2, 0.0, 0.0, 1.0, 0.0, -0.1],
      ]
    )
    assert numpy.all(int_best_one_hot_neighbors == correct_answers_int_best_one_hot_neighbors)

    cat_best_one_hot_neighbors = find_best_one_hot_neighbor_by_af(
      one_hot_points,
      self.mixed_domain,
      dummy_acquisition_function(),
      "cat",
    )
    correct_answers_cat_best_one_hot_neighbors = numpy.array(
      [
        [0.0, 0.0, 1.0, 3.0, -0.5, 17.0, -5.2, 0.0, 0.0, 0.0, 1.0, 0.2],
        [0.0, 0.0, 1.0, 4.0, -0.1, 20.0, 2.2, 0.0, 0.0, 0.0, 1.0, -0.1],
      ]
    )
    assert numpy.all(cat_best_one_hot_neighbors == correct_answers_cat_best_one_hot_neighbors)

    both_best_one_hot_neighbors = find_best_one_hot_neighbor_by_af(
      one_hot_points,
      self.mixed_domain,
      dummy_acquisition_function(),
      "both",
    )
    correct_answers_both_best_one_hot_neighbors = numpy.array(
      [
        [0.0, 0.0, 1.0, 3.0, -0.5, 18.0, -5.2, 0.0, 0.0, 0.0, 1.0, 0.2],
        [0.0, 0.0, 1.0, 5.0, -0.1, 20.0, 2.2, 0.0, 0.0, 0.0, 1.0, -0.1],
      ]
    )
    assert numpy.all(both_best_one_hot_neighbors == correct_answers_both_best_one_hot_neighbors)

    correct_cat_domain_points_given_dummy_acquisition_function = [
      [5, 3.0, -0.5, 18.0, -5.2, 9.0, 0.2],
      [5, 5.0, -0.1, 20.0, 2.2, 9.0, -0.1],
    ]
    converted_points = convert_from_one_hot(
      one_hot_points,
      self.mixed_domain,
      dummy_acquisition_function(),
      temperature=1e-2,
    )

    # This comparison is necessary because of the non_numerical categorical in the domain
    for p, true_p in zip(converted_points, correct_cat_domain_points_given_dummy_acquisition_function):
      assert tuple(p) == tuple(true_p)

  # NOTE: The use of tuples makes checking points easier
  # NOTE: This takes advantage of a known ordering of points during replacement that may not always be the case
  def test_replacing_non_unique_points(self):
    data = HistoricalData(self.mixed_domain.one_hot_dim)
    data.append_lies(self.mixed_domain.one_hot_domain.generate_quasi_random_points_in_domain(10), 0, 0)
    categorical_points = numpy.array(
      [
        (5.0, 3.0, -0.5, 18.0, -5.2, 2.0, 0.2),
        (3.0, 5.0, -0.1, 20.0, 2.2, 6.0, 0.5),
        (5.0, 3.0, -0.5 + 1e-6, 18.0, -5.2, 2.0, 0.2),
        (5.0, 3.0, -0.5, 18.0, -5.2, 2.0, 0.2 + 1e-7),
        (5.0, 3.0, -0.5, 18.0, -5.2, 2.0, 0.2),
        (-1.0, 2.0, 3.2, 12.0, 2.8, 9.0, 9),
      ]
    )
    data.append_lies([self.mixed_domain.map_categorical_point_to_one_hot(categorical_points[-1])], 0, 0)
    categorical_points_historical = self.mixed_domain.map_one_hot_points_to_categorical(data.points_sampled)
    unique_no_tol = [
      tuple(p) for p in self.mixed_domain.replace_duplicate_points(categorical_points, categorical_points_historical, 0)
    ]
    assert len(unique_no_tol) == 6
    assert all(p in unique_no_tol for p in [tuple(q) for q in categorical_points[:4]])
    assert not any(p in [tuple(q) for q in categorical_points] for p in unique_no_tol[4:])

    unique_tol = [
      tuple(p)
      for p in self.mixed_domain.replace_duplicate_points(categorical_points, categorical_points_historical, 1e-3)
    ]
    assert len(unique_tol) == 6
    assert all(p in unique_tol for p in [tuple(q) for q in categorical_points[:2]])
    assert not any(p in [tuple(q) for q in categorical_points] for p in unique_tol[2:])


class TestAugmentedDomain:
  tasks = numpy.array([0.5, 0.2, 1.0])

  def test_no_acquisition_function(self):
    domain = CategoricalDomain([{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]}])
    computed_domain = form_augmented_domain(domain)
    assert domains_approximately_equal(domain, computed_domain)

    augmented_domain_with_tasks = CategoricalDomain(
      [
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.2, 1]},
      ]
    )
    computed_domain = form_augmented_domain(domain, task_cost_populated=True, task_options=self.tasks)
    assert domains_approximately_equal(augmented_domain_with_tasks, computed_domain)

    domain_with_constraint = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.3, 2.2]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [5, 10]},
      ],
      constraint_list=[
        {"weights": [1.0, -0.5, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 1.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    computed_domain = form_augmented_domain(domain_with_constraint)
    assert domains_approximately_equal(domain_with_constraint, computed_domain)

    augmented_domain_with_constraint_with_tasks = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.3, 2.2]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [5, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.2, 1]},
      ],
      constraint_list=[
        {"weights": [1.0, -0.5, 0.0, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 1.0, 1.0, 0.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    computed_domain = form_augmented_domain(domain_with_constraint, task_cost_populated=True, task_options=self.tasks)
    assert domains_approximately_equal(augmented_domain_with_constraint_with_tasks, computed_domain)

  def test_with_acquisition_function(self):
    domain = CategoricalDomain(
      [
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ]
    )

    af = Mock(dim=6, num_points_to_sample=1)
    assert domains_approximately_equal(domain, form_augmented_domain(domain, acquisition_function=af))
    af.dim = 5
    with pytest.raises(AssertionError):
      form_augmented_domain(domain, acquisition_function=af)

    domain_with_appended_tasks = CategoricalDomain(
      [
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.2, 1.0]},
      ]
    )
    af = Mock(dim=7, num_points_to_sample=1)
    af.__class__ = MultitaskAcquisitionFunction
    computed_domain = form_augmented_domain(
      domain=domain,
      acquisition_function=af,
      task_cost_populated=True,
      task_options=self.tasks,
    )
    assert domains_approximately_equal(domain_with_appended_tasks, computed_domain)

  def test_with_constraints(self):
    domain_with_constraints = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4.5, -2.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 6]},
      ],
      constraint_list=[
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0], "rhs": 1.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    computed_domain = form_augmented_domain(domain_with_constraints)
    assert domains_approximately_equal(domain_with_constraints, computed_domain)

    domain_using_hitandrun = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4.5, -2.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 6]},
      ],
      constraint_list=[
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0], "rhs": 1.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
      force_hitandrun_sampling=True,
    )
    computed_domain = form_augmented_domain(domain_using_hitandrun)
    assert domains_approximately_equal(domain_using_hitandrun, computed_domain)

    # Technically, the ordering of constraints shouldn't matter (weight ordering matters) ... something to fix
    domain_with_two_points_with_constraints = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4.5, -2.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 6]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4.5, -2.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 6]},
      ],
      constraint_list=[
        {
          "weights": [1.0, 1.0, 0, -0.5, 0, 0, 0, 0, 0, 0, 0, 0],
          "rhs": 0.3,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
        },
        {
          "weights": [0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, -0.5, 0, 0],
          "rhs": 0.3,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
        },
        {
          "weights": [1.0, 1.0, 0, -0.5, 0, 0, 0, 0, 0, 0, 0, 0],
          "rhs": 1.3,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
        },
        {
          "weights": [0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, -0.5, 0, 0],
          "rhs": 1.3,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
        },
        {"weights": [0, 0, 0, 0, 1.0, 1.0, 0, 0, 0, 0, 0, 0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 1.0, 1.0, 0, 0, 0, 0, 0, 0], "rhs": 1.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0], "rhs": 1.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    af = Mock(dim=8, num_points_to_sample=2)
    computed_domain = form_augmented_domain(domain=domain_with_constraints, acquisition_function=af)
    assert domains_approximately_equal(domain_with_two_points_with_constraints, computed_domain)

    domain_with_constraints_and_tasks = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4.5, -2.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 6]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.2, 1.0]},
      ],
      constraint_list=[
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 1.0, 0.0, -0.5, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0], "rhs": 1.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    af = Mock(dim=9, num_points_to_sample=1)
    af.__class__ = MultitaskAcquisitionFunction
    computed_domain = form_augmented_domain(
      domain=domain_with_constraints,
      acquisition_function=af,
      task_cost_populated=True,
      task_options=self.tasks,
    )
    assert domains_approximately_equal(domain_with_constraints_and_tasks, computed_domain)
