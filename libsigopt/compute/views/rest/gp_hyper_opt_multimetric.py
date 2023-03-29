# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MINIMUM_VALUE_VAR,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.log_likelihood import GaussianProcessLogMarginalLikelihood
from libsigopt.compute.misc.constant import (
  DEFAULT_COVARIANCE_KERNEL,
  DISCRETE_UNIQUENESS_LENGTH_SCALE_MIN_BOUND,
  QUANTIZED_LENGTH_SCALE_LOWER_FACTOR,
  TASK_LENGTH_LOWER_BOUND,
)
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.optimization import MultistartOptimizer, SLSQPOptimizer
from libsigopt.compute.optimization_auxiliary import OptimizerInfo, SLSQPParameters
from libsigopt.compute.views.view import GPView


SELECT_HYPER_OPT_IN_LOG_DOMAIN = False
DEFAULT_HYPER_OPT_OPTIMIZER_INFO = OptimizerInfo(
  optimizer=SLSQPOptimizer,
  parameters=SLSQPParameters(ftol=1.0e-2),
  num_multistarts=10,
  num_random_samples=0,
)

# TODO(RTL-73): Consider alternate behavior for bounds, as these are simply our previous defaults
# NOTE: In reality, this var quantity should probably even be much higher
def form_one_hot_hyperparameter_domain(
  categorical_domain,
  historical_data,
  use_auto_noise,
  discrete_lower_limit,
  task_cost_populated,
  select_hyper_opt_in_log_domain=SELECT_HYPER_OPT_IN_LOG_DOMAIN,
):
  ALPHA_LOWER_FACTOR = 0.001
  ALPHA_UPPER_FACTOR = 10
  CATEGORICAL_UPPER_BOUND = 1.01
  LENGTH_SCALE_LOWER_FACTOR = 0.001
  LENGTH_SCALE_UPPER_FACTOR = 1
  TIKHONOV_LOWER_FACTOR = 0.0001
  TIKHONOV_UPPER_FACTOR = 100

  hyperparameter_domain_elements = []

  # NOTE: This nan should only occur if there is no data (maybe better to handle elsewhere or error?
  sample_variance = numpy.var(historical_data.points_sampled_value)
  sample_variance = MINIMUM_VALUE_VAR if numpy.isnan(sample_variance) else max(sample_variance, MINIMUM_VALUE_VAR)
  hyperparameter_domain_elements.append([ALPHA_LOWER_FACTOR * sample_variance, ALPHA_UPPER_FACTOR * sample_variance])

  for one_hot_mapping in categorical_domain.one_hot_to_categorical_mapping:
    if one_hot_mapping["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
      for _ in one_hot_mapping["input_ind_value_map"]:
        hyperparameter_domain_elements.append([discrete_lower_limit, CATEGORICAL_UPPER_BOUND])
    else:
      bounds = categorical_domain.domain_components[one_hot_mapping["output_ind"]]["elements"]
      width = bounds[-1] - bounds[0]
      lower_bound, upper_bound = LENGTH_SCALE_LOWER_FACTOR * width, LENGTH_SCALE_UPPER_FACTOR * width
      if one_hot_mapping["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
        lower_bound = max(discrete_lower_limit, lower_bound)
      elif one_hot_mapping["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
        lower_bound = max(QUANTIZED_LENGTH_SCALE_LOWER_FACTOR * min(numpy.diff(bounds)), lower_bound)

      hyperparameter_domain_elements.append([lower_bound, upper_bound])

  if task_cost_populated:
    hyperparameter_domain_elements.append([TASK_LENGTH_LOWER_BOUND, CATEGORICAL_UPPER_BOUND])

  if use_auto_noise:
    hyperparameter_domain_elements.append(
      [TIKHONOV_LOWER_FACTOR * sample_variance, TIKHONOV_UPPER_FACTOR * sample_variance],
    )

  if select_hyper_opt_in_log_domain:
    for these_elements in hyperparameter_domain_elements:
      these_elements[0], these_elements[1] = numpy.log(these_elements)

  domain_components = [
    {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": e} for e in hyperparameter_domain_elements
  ]
  return CategoricalDomain(domain_components).one_hot_domain


class GpHyperOptMultimetricView(GPView):
  view_name = "gp_hyper_opt_multimetric"

  @property
  def optimizer_info(self):
    return DEFAULT_HYPER_OPT_OPTIMIZER_INFO

  def should_skip_hyperopt(self, points_sampled_values):
    return numpy.ptp(points_sampled_values) <= MINIMUM_VALUE_VAR

  def view(self):
    model_info = deepcopy(self.params["model_info"])
    hyperparameters = deepcopy(model_info.hyperparameters)

    successful_indexes = numpy.logical_not(self.points_sampled_failures)
    one_hot_points_sampled_points = self.one_hot_points_sampled_points[successful_indexes, :]
    if self.has_optimization_metrics:
      for i, index in enumerate(self.optimized_metrics_index):
        points_sampled_values = self.points_sampled_for_af_values[successful_indexes, i]
        if self.should_skip_hyperopt(points_sampled_values):
          continue
        points_sampled_value_vars = self.points_sampled_for_af_value_vars[successful_indexes, i]
        hyperparameter_dict = self.params["model_info"].hyperparameters[index]
        hyperparameters[index] = self.call_hyperopt_per_metric(
          one_hot_points_sampled_points,
          points_sampled_values,
          points_sampled_value_vars,
          hyperparameter_dict,
        )

    if self.has_constraint_metrics:
      for i, index in enumerate(self.constraint_metrics_index):
        points_sampled_values = self.points_sampled_for_pf_values[successful_indexes, i]
        if self.should_skip_hyperopt(points_sampled_values):
          continue
        points_sampled_value_vars = self.points_sampled_for_pf_value_vars[successful_indexes, i]
        hyperparameter_dict = self.params["model_info"].hyperparameters[index]
        hyperparameters[index] = self.call_hyperopt_per_metric(
          one_hot_points_sampled_points,
          points_sampled_values,
          points_sampled_value_vars,
          hyperparameter_dict
        )
    self.tag.update({"optimizer_info": self.optimizer_info})
    return {
      "endpoint": self.view_name,
      "hyperparameter_dict": hyperparameters,
      "tag": self.tag,
    }

  def call_hyperopt_per_metric(
    self,
    one_hot_points_sampled_points,
    points_sampled_values,
    points_sampled_value_vars,
    hyperparameter_dict,
  ):

    one_hot_historical_data = HistoricalData(self.dim_with_task)
    one_hot_historical_data.append_historical_data(
      one_hot_points_sampled_points,
      points_sampled_values,
      points_sampled_value_vars,
    )
    one_hot_covariance = self.form_one_hot_covariance_base(
      self.domain,
      hyperparameter_dict,
    )

    use_auto_noise = hyperparameter_dict["tikhonov"] is not None

    # TODO(RTL-75): Decide if there are different ways to handle this for multitask
    one_hot_hyperparameter_domain = form_one_hot_hyperparameter_domain(
      self.domain,
      one_hot_historical_data,
      use_auto_noise,
      DISCRETE_UNIQUENESS_LENGTH_SCALE_MIN_BOUND[DEFAULT_COVARIANCE_KERNEL],
      self.task_cost_populated,
    )

    log_likelihood_eval = GaussianProcessLogMarginalLikelihood(
      one_hot_covariance,
      one_hot_historical_data,
      mean_poly_indices=self.polynomial_indices,
      use_auto_noise=use_auto_noise,
      log_domain=SELECT_HYPER_OPT_IN_LOG_DOMAIN,
    )

    log_likelihood_optimizer = self.optimizer_info.optimizer(
      one_hot_hyperparameter_domain,
      log_likelihood_eval,
      self.optimizer_info.parameters,
    )
    multistart_optimizer = MultistartOptimizer(
      log_likelihood_optimizer,
      num_multistarts=self.optimizer_info.num_multistarts,
      log_sample=not SELECT_HYPER_OPT_IN_LOG_DOMAIN,
    )
    optimized_hyperparameters, _ = multistart_optimizer.optimize(
      selected_starts=log_likelihood_eval.current_point[None, :]
    )

    # NOTE: Obviously, this enforces a specific structure on the hyperparameter vector
    optimized_hyperparameter_list = optimized_hyperparameters.tolist()
    alpha = optimized_hyperparameter_list.pop(0)
    tikhonov = optimized_hyperparameter_list.pop(-1) if use_auto_noise else None
    length_scales = self.domain.map_one_hot_length_scales_to_categorical(optimized_hyperparameter_list)
    task_length = optimized_hyperparameter_list.pop(-1) if self.task_cost_populated else None

    return {
      "alpha": alpha,
      "length_scales": length_scales,
      "task_length": task_length,
      "tikhonov": tikhonov,
    }
