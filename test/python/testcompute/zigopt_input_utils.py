# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.aux.adapter_info_containers import DomainInfo, GPModelInfo, MetricsInfo, PointsContainer
from libsigopt.aux.constant import CATEGORICAL_EXPERIMENT_PARAMETER_NAME, TASK_SELECTION_STRATEGY_A_PRIORI
from libsigopt.compute.domain import ContinuousDomain
from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE, NONZERO_MEAN_CUSTOM_MEAN_TYPE
from testaux.utils import form_random_unconstrained_categorical_domain


DEFAULT_NOISE_PER_POINT = 1e-10
TEST_FAILURE_PROB = 0.1


# TODO(RTL-96): Clean this up to have a minimum number of points in the domain
def form_random_hyperparameter_dict(domain, use_tikhonov=False, add_task_length=False, num_metrics=1):
  list_of_hyperparameter_dict = []
  for _ in range(num_metrics):
    alpha = numpy.random.gamma(1, 0.1)
    tikhonov = numpy.random.gamma(1, 0.1) if use_tikhonov else None
    task_length = 0.19 if add_task_length else None
    length_scales = []
    for dc in domain:
      if dc["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        length_scales.append(numpy.random.uniform(0.5, 2.0, len(dc["elements"])).tolist())
      else:
        length_scales.append([numpy.random.gamma(1, 0.1) * (dc["elements"][1] - dc["elements"][0])])
    list_of_hyperparameter_dict.append(
      {
        "alpha": alpha,
        "length_scales": length_scales,
        "tikhonov": tikhonov,
        "task_length": task_length,
      }
    )
  return list_of_hyperparameter_dict


def form_domain_info(domain):
  return DomainInfo(
    constraint_list=domain.constraint_list,
    domain_components=domain.domain_components,
    force_hitandrun_sampling=domain.force_hitandrun_sampling,
    priors=domain.priors,
  )


def form_model_info(
  domain,
  task_options,
  num_metrics,
  nonzero_mean_type,
  use_tikhonov,
):
  return GPModelInfo(
    hyperparameters=form_random_hyperparameter_dict(
      domain,
      add_task_length=task_options.size,
      num_metrics=num_metrics,
      use_tikhonov=use_tikhonov,
    ),
    max_simultaneous_af_points=5432,
    nonzero_mean_info=form_nonzero_mean_data(domain.dim, nonzero_mean_type),
    task_selection_strategy=TASK_SELECTION_STRATEGY_A_PRIORI if task_options.size else None,
  )


def form_nonzero_mean_data(dim, mean_type):
  if mean_type == NONZERO_MEAN_CUSTOM_MEAN_TYPE:
    raise ValueError("This will need some work to make work with tasks")
    # return {'mean_type': NONZERO_MEAN_CUSTOM_MEAN_TYPE, 'poly_indices': numpy.random.randint(0, 3, dim)}
  return {"mean_type": mean_type, "poly_indices": None}


# NOTE: Some potential issues with snap_cats as this is currently constructed
def form_points_sampled(
  domain,
  num_sampled,
  noise_per_point,
  num_metrics,
  task_options,
  snap_cats=False,
  failure_prob=TEST_FAILURE_PROB,
):
  points = domain.generate_quasi_random_points_in_domain(num_sampled)
  if isinstance(domain, ContinuousDomain) and snap_cats:
    for k, this_closed_interval in enumerate(domain.domain_bounds):
      if numpy.all(this_closed_interval == numpy.array([0, 1])):
        points[:, k] = numpy.round(points[:, k])
  values = numpy.random.uniform(-0.1, 0.1, (num_sampled, num_metrics))
  failures = numpy.random.random(num_sampled) < failure_prob

  return PointsContainer(
    points=points,
    values=values,
    value_vars=numpy.full_like(values, noise_per_point),
    failures=failures,
    task_costs=numpy.random.choice(task_options, size=failures.shape) if task_options.size else None,
  )


def form_points_being_sampled(domain, num_points_being_sampled, task_options=None):
  return PointsContainer(
    points=domain.generate_quasi_random_points_in_domain(num_points_being_sampled),
    task_costs=numpy.random.choice(task_options, size=num_points_being_sampled) if task_options.size else None,
  )


form_points_to_evaluate = form_points_being_sampled


def form_metrics_info(
  num_optimized_metrics,
  num_constraint_metrics,
  num_stored_metrics,
  metric_objectives,
  optimized_metric_thresholds=None,
  constraint_metric_thresholds=None,
):
  num_metrics = num_optimized_metrics + num_constraint_metrics + num_stored_metrics
  shuffled_index = numpy.random.permutation(numpy.arange(num_metrics, dtype=int))
  optimized_metrics_index = shuffled_index[:num_optimized_metrics]
  constraint_metrics_index = shuffled_index[num_optimized_metrics : num_optimized_metrics + num_constraint_metrics]

  user_specified_thresholds = numpy.full(num_metrics, numpy.nan)
  assert optimized_metric_thresholds is None or num_optimized_metrics == len(optimized_metric_thresholds)
  assert constraint_metric_thresholds is None or num_constraint_metrics == len(constraint_metric_thresholds)
  if optimized_metric_thresholds is not None:
    user_specified_thresholds[optimized_metrics_index] = optimized_metric_thresholds
  if constraint_metric_thresholds is not None:
    user_specified_thresholds[constraint_metrics_index] = constraint_metric_thresholds

  requires_pareto_frontier_optimization = False
  if num_optimized_metrics == 2:
    requires_pareto_frontier_optimization = True

  if not metric_objectives:
    metric_objectives = ["maximize" for _ in range(num_metrics)]
  return MetricsInfo(
    requires_pareto_frontier_optimization=requires_pareto_frontier_optimization,
    observation_budget=numpy.random.randint(50, 200),
    user_specified_thresholds=user_specified_thresholds,
    objectives=metric_objectives,
    optimized_metrics_index=optimized_metrics_index,
    constraint_metrics_index=constraint_metrics_index,
  )


class ZigoptSimulator(object):
  def __init__(
    self,
    dim,
    num_sampled,
    num_optimized_metrics=1,
    num_constraint_metrics=0,
    num_stored_metrics=0,
    num_to_sample=0,
    num_being_sampled=0,
    noise_per_point=DEFAULT_NOISE_PER_POINT,
    nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
    use_tikhonov=False,
    num_tasks=0,
    failure_prob=TEST_FAILURE_PROB,
    metric_objectives=None,
    optimized_metric_thresholds=None,
    constraint_metric_thresholds=None,
  ):
    self.dim = dim
    self.num_sampled = num_sampled
    self.num_to_sample = num_to_sample
    self.num_being_sampled = num_being_sampled
    self.nonzero_mean_type = nonzero_mean_type
    self.noise_per_point = noise_per_point
    self.num_metrics = num_optimized_metrics + num_constraint_metrics + num_stored_metrics
    self.use_tikhonov = use_tikhonov
    self.failure_prob = failure_prob
    self.metric_objectives = metric_objectives
    self.num_optimized_metrics = num_optimized_metrics
    self.num_constraint_metrics = num_constraint_metrics
    self.num_stored_metrics = num_stored_metrics
    self.optimized_metric_thresholds = optimized_metric_thresholds
    self.constraint_metric_thresholds = constraint_metric_thresholds
    self.num_tasks = num_tasks

  def form_gp_ei_categorical_inputs(self, parallelism_method):
    task_options = numpy.sort(numpy.random.random(self.num_tasks) if self.num_tasks else [])
    domain = form_random_unconstrained_categorical_domain(self.dim)
    points_sampled = form_points_sampled(
      domain,
      self.num_sampled,
      self.noise_per_point,
      self.num_metrics,
      task_options,
      failure_prob=self.failure_prob,
    )
    points_to_evaluate = form_points_to_evaluate(domain, self.num_to_sample, task_options=task_options)
    points_being_sampled = form_points_being_sampled(
      domain,
      self.num_being_sampled,
      task_options=task_options,
    )
    model_info = form_model_info(
      domain,
      task_options,
      self.num_metrics,
      self.nonzero_mean_type,
      self.use_tikhonov,
    )

    view_input = {
      "domain_info": form_domain_info(domain),
      "model_info": model_info,
      "parallelism": parallelism_method,
      "points_being_sampled": points_being_sampled,
      "points_sampled": points_sampled,
      "points_to_evaluate": points_to_evaluate,
      "tag": {"experiment_id": -1},
      "metrics_info": form_metrics_info(
        self.num_optimized_metrics,
        self.num_constraint_metrics,
        self.num_stored_metrics,
        self.metric_objectives,
        self.optimized_metric_thresholds,
        self.constraint_metric_thresholds,
      ),
      "task_options": task_options,
    }

    return view_input

  def form_gp_next_points_view_input_from_domain(self, domain, parallelism_method):
    task_options = numpy.sort(numpy.random.random(self.num_tasks) if self.num_tasks else [])
    points_sampled = form_points_sampled(
      domain,
      self.num_sampled,
      self.noise_per_point,
      self.num_metrics,
      task_options,
      failure_prob=self.failure_prob,
    )
    points_being_sampled = form_points_being_sampled(
      domain,
      self.num_being_sampled,
      task_options=task_options,
    )
    model_info = form_model_info(
      domain,
      task_options,
      self.num_metrics,
      self.nonzero_mean_type,
      self.use_tikhonov,
    )

    view_input = {
      "domain_info": form_domain_info(domain),
      "model_info": model_info,
      "num_to_sample": self.num_to_sample,
      "parallelism": parallelism_method,
      "points_sampled": points_sampled,
      "points_being_sampled": points_being_sampled,
      "tag": {"experiment_id": -1},
      "metrics_info": form_metrics_info(
        self.num_optimized_metrics,
        self.num_constraint_metrics,
        self.num_stored_metrics,
        self.metric_objectives,
        self.optimized_metric_thresholds,
        self.constraint_metric_thresholds,
      ),
      "task_options": task_options,
    }
    return view_input

  def form_gp_next_points_categorical_inputs(self, parallelism_method):
    domain = form_random_unconstrained_categorical_domain(self.dim)
    view_input = self.form_gp_next_points_view_input_from_domain(domain, parallelism_method)
    return view_input, domain

  def form_search_next_points_view_input_from_domain(self, domain, parallelism_method):
    view_input = self.form_gp_next_points_view_input_from_domain(domain, parallelism_method)
    return view_input, domain

  def form_search_next_points_categorical_inputs(self, parallelism_method):
    domain = form_random_unconstrained_categorical_domain(self.dim)
    view_input = self.form_gp_next_points_view_input_from_domain(domain, parallelism_method)
    return view_input, domain

  def form_spe_next_points_view_input_from_domain(self, domain):
    task_options = numpy.sort(numpy.random.random(self.num_tasks) if self.num_tasks else [])
    points_sampled = form_points_sampled(
      domain,
      self.num_sampled,
      self.noise_per_point,
      self.num_metrics,
      task_options,
      failure_prob=self.failure_prob,
    )
    points_being_sampled = form_points_being_sampled(
      domain,
      self.num_being_sampled,
      task_options=task_options,
    )

    view_input = {
      "domain_info": form_domain_info(domain),
      "max_simultaneous_af_points": 1000,
      "num_to_sample": self.num_to_sample,
      "points_sampled": points_sampled,
      "points_being_sampled": points_being_sampled,
      "tag": {"experiment_id": -1},
      "metrics_info": form_metrics_info(
        self.num_optimized_metrics,
        self.num_constraint_metrics,
        self.num_stored_metrics,
        self.metric_objectives,
        self.optimized_metric_thresholds,
        self.constraint_metric_thresholds,
      ),
      "task_options": task_options,
    }
    view_input["metrics_info"].observation_budget = numpy.random.randint(50, 200)

    return view_input

  def form_spe_next_points_inputs(self):
    domain = form_random_unconstrained_categorical_domain(self.dim)
    view_input = self.form_spe_next_points_view_input_from_domain(domain)
    return view_input, domain

  def form_spe_search_next_points_inputs(self):
    domain = form_random_unconstrained_categorical_domain(self.dim)
    view_input = self.form_spe_next_points_view_input_from_domain(domain)
    return view_input, domain

  def form_gp_hyper_opt_categorical_inputs(self):
    task_options = numpy.sort(numpy.random.random(self.num_tasks) if self.num_tasks else [])
    domain = form_random_unconstrained_categorical_domain(self.dim)
    points_sampled = form_points_sampled(
      domain,
      self.num_sampled,
      self.noise_per_point,
      self.num_metrics,
      task_options,
      failure_prob=self.failure_prob,
    )
    model_info = form_model_info(
      domain,
      task_options,
      self.num_metrics,
      self.nonzero_mean_type,
      self.use_tikhonov,
    )

    view_input = {
      "domain_info": form_domain_info(domain),
      "model_info": model_info,
      "points_sampled": points_sampled,
      "tag": {"experiment_id": -1},
      "metrics_info": form_metrics_info(
        self.num_optimized_metrics,
        self.num_constraint_metrics,
        self.num_stored_metrics,
        self.metric_objectives,
        self.optimized_metric_thresholds,
        self.constraint_metric_thresholds,
      ),
      "task_options": task_options,
    }

    return view_input, domain
