# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
from dataclasses import asdict

import numpy

from libsigopt.aux.adapter_info_containers import GPModelInfo
from libsigopt.aux.constant import PARALLEL_CONSTANT_LIAR
from libsigopt.compute.covariance import COVARIANCE_TYPES_TO_CLASSES
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.expected_improvement import (
  AugmentedExpectedImprovement,
  ExpectedImprovement,
  ExpectedImprovementWithFailures,
  ExpectedParallelImprovement,
  ExpectedParallelImprovementWithFailures,
)
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.gaussian_process_sum import GaussianProcessSum
from libsigopt.compute.misc.constant import (
  CONSTANT_LIAR_MIN,
  DEFAULT_CONSTANT_LIAR_LIE_NOISE_VARIANCE,
  DEFAULT_COVARIANCE_KERNEL,
  DEFAULT_TASK_COVARIANCE_KERNEL,
)
from libsigopt.compute.misc.data_containers import HistoricalData, MultiMetricMidpointInfo, SingleMetricMidpointInfo
from libsigopt.compute.misc.multimetric import (
  CONVEX_COMBINATION,
  EPSILON_CONSTRAINT,
  MULTIMETRIC_INFO_NOT_MULTIMETRIC,
  PROBABILISTIC_FAILURES,
  filter_multimetric_points_sampled,
  find_epsilon_constraint_value,
  form_multimetric_info_from_phase,
  identify_multimetric_phase,
)
from libsigopt.compute.multitask_covariance import MultitaskTensorCovariance
from libsigopt.compute.probabilistic_failures import (
  ProbabilisticFailures,
  ProbabilisticFailuresCDF,
  ProductOfListOfProbabilisticFailures,
)
from libsigopt.compute.python_utils import validate_polynomial_indices


_UNSET = object()
# Level of noise at which Augmented Expected Improvement should be used
AUGMENTED_EI_THRESHOLD = 1e-7


def filter_points_sampled(points_sampled, metrics_info):
  optimized_metrics_index = numpy.asarray(metrics_info.optimized_metrics_index)
  has_optimization_metrics = metrics_info.has_optimization_metrics
  has_constraint_metrics = metrics_info.has_constraint_metrics
  constraint_metrics_index = False
  if has_constraint_metrics:
    constraint_metrics_index = numpy.asarray(metrics_info.constraint_metrics_index)

  return (
    points_sampled.points,
    points_sampled.values[:, optimized_metrics_index] if has_optimization_metrics else _UNSET,
    points_sampled.value_vars[:, optimized_metrics_index] if has_optimization_metrics else _UNSET,
    points_sampled.values[:, constraint_metrics_index] if has_constraint_metrics else _UNSET,
    points_sampled.value_vars[:, constraint_metrics_index] if has_constraint_metrics else _UNSET,
    points_sampled.failures,
    points_sampled.task_costs,
  )


def form_one_hot_points_with_tasks(domain, points, task_costs=None):
  assert isinstance(domain, CategoricalDomain)
  one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in points])
  if task_costs is not None and one_hot_points.size:
    one_hot_points = numpy.concatenate((one_hot_points, task_costs[:, None]), axis=1)
  return one_hot_points


def form_metric_midpoint_info(points_sampled_values, points_sampled_failures, metric_objectives):
  if len(points_sampled_values.shape) == 1:
    mmi = SingleMetricMidpointInfo(points_sampled_values, points_sampled_failures, metric_objectives)
  else:
    mmi = MultiMetricMidpointInfo(points_sampled_values, points_sampled_failures, metric_objectives)
  return mmi


def identify_scaled_values_exceeding_scaled_upper_thresholds(scaled_values, scaled_upper_thresholds):
  within_bounds = numpy.full(len(scaled_values), True, dtype=bool)
  for i, scaled_upper_threshold in enumerate(scaled_upper_thresholds):
    if not numpy.isnan(scaled_upper_threshold):
      within_bounds = numpy.logical_and(within_bounds, scaled_values[:, i] < scaled_upper_threshold)
  return numpy.logical_not(within_bounds)


def get_relevant_expected_improvement(predictor):
  # If mean of sample variances is above threshold we use Augmented Expected Improvement
  noise_variance = numpy.mean(predictor.points_sampled_noise_variance)
  if noise_variance > AUGMENTED_EI_THRESHOLD:
    return AugmentedExpectedImprovement(predictor)
  else:
    return ExpectedImprovement(predictor)


class View(object):
  view_name = None

  def __init__(self, params, logging_service=None):
    self.params = params
    self.log = (logging_service or logging).getLogger(__name__)
    self.tag = self.params["tag"]

    self.domain = CategoricalDomain(**asdict(self.params["domain_info"]))
    self.task_options = numpy.array(self.params["task_options"])
    self.task_cost_populated = self.task_options.size

    self.optimized_metrics_index = _UNSET
    self.optimized_metrics_objectives = _UNSET
    self._mmi = _UNSET
    self.optimized_metrics_thresholds = _UNSET
    self.scaled_optimized_lie_values = _UNSET

    self.constraint_metrics_index = _UNSET
    self.constraint_metrics_objectives = _UNSET
    self._constraint_mmi = _UNSET
    self.scaled_constraint_lie_values = _UNSET

    self.has_optimization_metrics = self.params["metrics_info"].has_optimization_metrics
    self.has_constraint_metrics = self.params["metrics_info"].has_constraint_metrics

    if not self.has_optimization_metrics:
      assert len(self.params["metrics_info"].optimized_metrics_index) == 0
    assert self.has_optimization_metrics or self.has_constraint_metrics

    (
      self.points_sampled_points,
      self.points_sampled_for_af_values,
      self.points_sampled_for_af_value_vars,
      self.points_sampled_for_pf_values,
      self.points_sampled_for_pf_value_vars,
      self.points_sampled_failures,
      self.points_sampled_task_costs,
    ) = filter_points_sampled(
      self.params["points_sampled"],
      self.params["metrics_info"],
    )
    if not self.task_cost_populated:
      assert self.points_sampled_task_costs is None

    if self.has_optimization_metrics:
      self._preprocess_optimization_metrics()

    if self.has_constraint_metrics:
      self._preprocess_constraint_metrics()

    # Convert to one hot point space
    self.one_hot_points_sampled_points = form_one_hot_points_with_tasks(
      self.domain,
      self.points_sampled_points,
      self.points_sampled_task_costs,
    )

    self._one_hot_points_being_sampled_points = _UNSET
    self._one_hot_points_to_evaluate_points = _UNSET
    self.dim_with_task = self.one_hot_points_sampled_points.shape[1]
    assert self.dim_with_task == self.domain.one_hot_dim + (1 if self.task_cost_populated else 0)

    self.form_multimetric_info()

  # TODO: these two preprocess functions have a lot of overlap, consolidate this later.
  def _preprocess_optimization_metrics(self):
    self.optimized_metrics_index = self.params["metrics_info"].optimized_metrics_index
    assert len(self.optimized_metrics_index) >= 1
    self.optimized_metrics_objectives = numpy.asarray(
      self.params["metrics_info"].objectives,
      dtype=str,
    )[self.optimized_metrics_index].tolist()
    assert len(self.optimized_metrics_objectives) == len(self.optimized_metrics_index)
    self._mmi = form_metric_midpoint_info(
      self.points_sampled_for_af_values,
      self.points_sampled_failures,
      self.optimized_metrics_objectives,
    )

    # invert and scale points_sampled_value and points_sampled_value_vars
    self.scaled_optimized_lie_values = self._mmi.relative_objective_value(
      self._mmi.compute_lie_value(CONSTANT_LIAR_MIN)
    )
    self.points_sampled_for_af_values = self._mmi.relative_objective_value(self.points_sampled_for_af_values)
    self.points_sampled_for_af_values[self.points_sampled_failures] = self.scaled_optimized_lie_values
    self.points_sampled_for_af_value_vars = self._mmi.relative_objective_variance(self.points_sampled_for_af_value_vars)
    unscaled_optimized_metrics_thresholds = numpy.asarray(
      self.params["metrics_info"].user_specified_thresholds,
      dtype=float,
    )[self.optimized_metrics_index]
    self.optimized_metrics_thresholds = self._mmi.relative_objective_value(unscaled_optimized_metrics_thresholds)

  def _preprocess_constraint_metrics(self):
    self.constraint_metrics_index = self.params["metrics_info"].constraint_metrics_index
    assert len(self.constraint_metrics_index) >= 1
    self.constraint_metrics_objectives = numpy.asarray(
      self.params["metrics_info"].objectives,
      dtype=str,
    )[self.constraint_metrics_index].tolist()
    assert len(self.constraint_metrics_objectives) == len(self.constraint_metrics_index)
    self._constraint_mmi = form_metric_midpoint_info(
      self.points_sampled_for_pf_values,
      self.points_sampled_failures,
      self.constraint_metrics_objectives,
    )
    self.scaled_constraint_lie_values = self._constraint_mmi.relative_objective_value(
      self._constraint_mmi.compute_lie_value(CONSTANT_LIAR_MIN)
    )
    self.points_sampled_for_pf_values = self._constraint_mmi.relative_objective_value(self.points_sampled_for_pf_values)
    self.points_sampled_for_pf_values[self.points_sampled_failures] = self.scaled_constraint_lie_values
    self.points_sampled_for_pf_value_vars = self._constraint_mmi.relative_objective_variance(
      self.points_sampled_for_pf_value_vars
    )
    unscaled_constraint_thresholds = numpy.asarray(
      self.params["metrics_info"].user_specified_thresholds,
      dtype=float,
    )[self.constraint_metrics_index]
    self.constraint_thresholds = self._constraint_mmi.relative_objective_value(unscaled_constraint_thresholds)

  @property
  def one_hot_points_to_evaluate_points(self):
    if self._one_hot_points_to_evaluate_points is _UNSET:
      self._one_hot_points_to_evaluate_points = form_one_hot_points_with_tasks(
        self.domain,
        self.params["points_to_evaluate"].points,
        self.params["points_to_evaluate"].task_costs if self.task_cost_populated else None,
      )
    return self._one_hot_points_to_evaluate_points

  @property
  def one_hot_points_being_sampled_points(self):
    if self._one_hot_points_being_sampled_points is _UNSET:
      self._one_hot_points_being_sampled_points = form_one_hot_points_with_tasks(
        self.domain,
        self.params["points_being_sampled"].points,
        self.params["points_being_sampled"].task_costs if self.task_cost_populated else None,
      )
    return self._one_hot_points_being_sampled_points

  def create_compute_log_line(self, log_type, content):
    self.log.info(
      "%s",
      dict(
        endpoint=self.view_name,
        type=log_type,
        content=content,
      ),
    )

  def call(self):
    self.create_compute_log_line("params", self.params)
    response = self.view()
    self.create_compute_log_line("return", response)
    return response

  def view(self):
    raise NotImplementedError()

  def form_multimetric_info(self):
    if not self.params["metrics_info"].requires_pareto_frontier_optimization:
      self.multimetric_info = MULTIMETRIC_INFO_NOT_MULTIMETRIC
      return

    num_open_suggestions = 0
    if "points_being_sampled" in self.params:
      num_open_suggestions = len(self.one_hot_points_being_sampled_points)
    phase, kwargs = identify_multimetric_phase(
      self.params["metrics_info"].has_optimized_metric_thresholds,
      self.params["metrics_info"].observation_budget,
      len(self.params["points_sampled"].points),
      numpy.sum(self.params["points_sampled"].failures),
      num_open_suggestions,
    )
    self.multimetric_info = form_multimetric_info_from_phase(phase, kwargs)


class GPView(View):
  def __init__(self, params, logging_service=None):
    super().__init__(params, logging_service)
    assert isinstance(self.params["model_info"], GPModelInfo)
    self._polynomial_indices = _UNSET

  @property
  def polynomial_indices(self):
    if self._polynomial_indices is _UNSET:
      self._polynomial_indices = self._compute_polynomial_indices()
    return self._polynomial_indices

  def _compute_polynomial_indices(self):
    return validate_polynomial_indices(
      self.params["model_info"].nonzero_mean_info["poly_indices"],
      self.params["model_info"].nonzero_mean_info["mean_type"],
      self.dim_with_task,
    )

  def form_one_hot_covariance_base(self, domain, hyperparameter_dict):
    assert isinstance(domain, CategoricalDomain)
    length_scales = hyperparameter_dict["length_scales"]

    one_hot_length_scales = domain.map_categorical_length_scales_to_one_hot(length_scales)
    hyperparameters = (
      [hyperparameter_dict["alpha"]]
      + one_hot_length_scales
      + ([] if hyperparameter_dict["task_length"] is None else [hyperparameter_dict["task_length"]])
    )

    physical_covariance_class = COVARIANCE_TYPES_TO_CLASSES[DEFAULT_COVARIANCE_KERNEL]
    if self.task_cost_populated:
      task_covariance_class = COVARIANCE_TYPES_TO_CLASSES[DEFAULT_TASK_COVARIANCE_KERNEL]
      covariance = MultitaskTensorCovariance(hyperparameters, physical_covariance_class, task_covariance_class)
    else:
      covariance = physical_covariance_class(hyperparameters)

    return covariance

  def form_single_gaussian_process(
    self,
    filtered_one_hot_points_sampled_points,
    filtered_points_sampled_values,
    filtered_points_sampled_value_vars,
    filtered_scaled_lie_value,
    hyperparameter_dict,
  ):
    one_hot_historical_data = HistoricalData(self.dim_with_task)
    one_hot_historical_data.append_historical_data(
      filtered_one_hot_points_sampled_points,
      filtered_points_sampled_values,
      filtered_points_sampled_value_vars,
    )
    if self.params["parallelism"] == PARALLEL_CONSTANT_LIAR:
      one_hot_historical_data.append_lies(
        self.one_hot_points_being_sampled_points,
        filtered_scaled_lie_value,
        DEFAULT_CONSTANT_LIAR_LIE_NOISE_VARIANCE,
      )

    one_hot_covariance = self.form_one_hot_covariance_base(
      self.domain,
      hyperparameter_dict,
    )

    gaussian_process = GaussianProcess(
      covariance=one_hot_covariance,
      historical_data=one_hot_historical_data,
      mean_poly_indices=self.polynomial_indices,
      tikhonov_param=hyperparameter_dict["tikhonov"],
    )
    return gaussian_process

  def form_gaussian_process_for_acquisition_function(self):
    (
      filtered_one_hot_points_sampled_points,
      filtered_points_sampled_values,
      filtered_points_sampled_value_vars,
      filtered_scaled_lie_value,
    ) = filter_multimetric_points_sampled(
      self.multimetric_info,
      self.one_hot_points_sampled_points,
      self.points_sampled_for_af_values,
      self.points_sampled_for_af_value_vars,
      self.points_sampled_failures,
      self.scaled_optimized_lie_values,
    )
    num_models = filtered_points_sampled_values.ndim
    if self.multimetric_info.method == CONVEX_COMBINATION:
      gaussian_process_list = []
      for i, metric_index in enumerate(self.optimized_metrics_index):
        gp = self.form_single_gaussian_process(
          filtered_one_hot_points_sampled_points,
          filtered_points_sampled_values[:, i],
          filtered_points_sampled_value_vars[:, i],
          filtered_scaled_lie_value[i],
          self.params["model_info"].hyperparameters[metric_index],
        )
        gaussian_process_list.append(gp)
      weights = numpy.copy(self.multimetric_info.params.weights)
      main_gaussian_process = GaussianProcessSum(gaussian_process_list, weights)
    else:
      assert num_models == 1
      optimization_model_index = 0
      if self.params["metrics_info"].requires_pareto_frontier_optimization:
        optimization_model_index = self.multimetric_info.params.optimizing_metric
      metric_index = self.optimized_metrics_index[optimization_model_index]
      main_gaussian_process = self.form_single_gaussian_process(
        filtered_one_hot_points_sampled_points,
        filtered_points_sampled_values,
        filtered_points_sampled_value_vars,
        filtered_scaled_lie_value,
        self.params["model_info"].hyperparameters[metric_index],
      )
    return main_gaussian_process

  def _form_gp_for_probabilistic_failures(self, relative_index, for_af_values=True):
    metric_indexes = self.optimized_metrics_index
    points_sampled_values = self.points_sampled_for_af_values
    points_sampled_value_vars = self.points_sampled_for_af_value_vars
    scaled_lie_values = self.scaled_optimized_lie_values
    if for_af_values:
      assert relative_index in (0, 1)
    else:
      assert relative_index in range(len(self.constraint_metrics_index))
      metric_indexes = self.constraint_metrics_index
      points_sampled_values = self.points_sampled_for_pf_values
      points_sampled_value_vars = self.points_sampled_for_pf_value_vars
      scaled_lie_values = self.scaled_constraint_lie_values

    return self.form_single_gaussian_process(
      self.one_hot_points_sampled_points,
      points_sampled_values[:, relative_index],
      points_sampled_value_vars[:, relative_index],
      scaled_lie_values[relative_index],
      self.params["model_info"].hyperparameters[metric_indexes[relative_index]],
    )

  # TODO(RTL-85): I think a lot of this workflow can be cleanup up with find_epsilon_constraint_value better now
  def _form_probabilistic_failures_for_pareto_frontier_optimization(self):
    multimetric_info = self.multimetric_info
    if multimetric_info.method not in (PROBABILISTIC_FAILURES, EPSILON_CONSTRAINT):
      return []

    constraint_metrics_index = multimetric_info.params.constraint_metric
    constraint_threshold = find_epsilon_constraint_value(
      multimetric_info.params.epsilon,
      constraint_metrics_index,
      self.points_sampled_for_af_values,
      self.optimized_metrics_thresholds,
    )

    threshold_0 = threshold_1 = None
    if not numpy.any(numpy.isnan(self.optimized_metrics_thresholds)) and len(self.optimized_metrics_thresholds) == 2:
      threshold_0, threshold_1 = self.optimized_metrics_thresholds
    if constraint_metrics_index == 0:
      threshold_0 = constraint_threshold
    else:
      threshold_1 = constraint_threshold

    pof_0 = None
    if threshold_0 is not None:
      gp = self._form_gp_for_probabilistic_failures(0, for_af_values=True)
      pof_0 = ProbabilisticFailures(gp, threshold_0)

    pof_1 = None
    if threshold_1 is not None:
      gp = self._form_gp_for_probabilistic_failures(1, for_af_values=True)
      pof_1 = ProbabilisticFailures(gp, threshold_1)

    if pof_0 is None:
      return [pof_1]
    if pof_1 is None:
      return [pof_0]
    return [pof_0, pof_1]

  def _form_list_of_probabilistic_failures_for_constraint_metrics(self):
    list_of_probabilistic_failures = []

    for i in range(len(self.constraint_metrics_index)):
      gp = self._form_gp_for_probabilistic_failures(i, for_af_values=False)
      threshold = self.constraint_thresholds[i]
      pof = ProbabilisticFailuresCDF(gp, threshold)
      list_of_probabilistic_failures.append(pof)

    return list_of_probabilistic_failures

  def form_probabilistic_failures_model(self):
    if not (
      self.multimetric_info.method in (PROBABILISTIC_FAILURES, EPSILON_CONSTRAINT) or self.has_constraint_metrics
    ):
      return None

    list_of_failures = self._form_probabilistic_failures_for_pareto_frontier_optimization()
    if self.has_constraint_metrics:
      list_of_failures.extend(self._form_list_of_probabilistic_failures_for_constraint_metrics())

    return ProductOfListOfProbabilisticFailures(list_of_failures)

  def _form_parallel_ei(self, gaussian_process, probabilistic_failures):
    num_to_sample = self.params.get("num_to_sample", 1)
    assert num_to_sample == 1, "Currently capping number of qEI suggestions to 1"
    if probabilistic_failures:
      self.tag.update({"failure_model_info": probabilistic_failures.info_for_logs})
      return ExpectedParallelImprovementWithFailures(
        predictor=gaussian_process,
        num_points_to_sample=num_to_sample,
        failure_model=probabilistic_failures,
        points_being_sampled=self.one_hot_points_being_sampled_points,
      )
    return ExpectedParallelImprovement(
      predictor=gaussian_process,
      num_points_to_sample=num_to_sample,
      points_being_sampled=self.one_hot_points_being_sampled_points,
    )

  def form_acquisition_function(self, gaussian_process, probabilistic_failures, use_parallel_ei):
    if use_parallel_ei:
      return self._form_parallel_ei(gaussian_process, probabilistic_failures)
    if probabilistic_failures:
      self.tag.update({"failure_model_info": probabilistic_failures.info_for_logs})
      return ExpectedImprovementWithFailures(
        predictor=gaussian_process,
        failure_model=probabilistic_failures,
      )
    return get_relevant_expected_improvement(gaussian_process)
