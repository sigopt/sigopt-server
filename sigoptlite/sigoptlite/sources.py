# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import asdict

import numpy

from libsigopt.aux.adapter_info_containers import DomainInfo, GPModelInfo, MetricsInfo, PointsContainer
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DEFAULT_HYPERPARAMETER_ALPHA,
  DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MAX_SIMULTANEOUS_AF_POINTS,
  MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
  PARALLEL_CONSTANT_LIAR,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
  ConstraintType,
  ParameterPriorNames,
  ParameterTransformationNames,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.views.rest.gp_hyper_opt_multimetric import GpHyperOptMultimetricView
from libsigopt.compute.views.rest.gp_next_points_categorical import GpNextPointsCategorical
from libsigopt.compute.views.rest.multisolution_best_assignments import MultisolutionBestAssignments
from libsigopt.compute.views.rest.search_next_points import SearchNextPoints
from libsigopt.compute.views.rest.spe_next_points import SPENextPoints
from libsigopt.compute.views.rest.spe_search_next_points import SPESearchNextPoints
from sigoptlite.builders import create_experiment_from_template
from sigoptlite.models import LocalSuggestion, dataclass_to_dict, replacement_value_if_missing


EMPTY_POINTS_CONTAINER = PointsContainer(points=numpy.array([]))


class BaseOptimizationSource(object):
  def __init__(self, experiment):
    self._original_experiment = experiment
    self.experiment = self.apply_transformations_to_experiment(experiment)

  def next_point(self, observations):
    raise NotImplementedError()

  def apply_transformations_to_experiment(self, original_experiment):
    if not original_experiment.is_conditional:
      return original_experiment
    return self.apply_conditional_transformation_to_experiment(original_experiment)

  def remove_transformations_from_source_suggestion(self, source_suggestion):
    if not self._original_experiment.is_conditional:
      return source_suggestion
    return self.remove_conditional_transformation_from_suggestion(self._original_experiment, source_suggestion)

  def get_suggestion(self, observations):
    suggested_point, suggested_task_cost = self.next_point(observations)
    assignments = self.make_assignments_from_point(self.experiment, suggested_point)
    task = self.get_task_by_cost(self.experiment, suggested_task_cost) if self.experiment.is_multitask else None
    source_suggestion = LocalSuggestion(assignments=assignments, task=task)
    return self.remove_transformations_from_source_suggestion(source_suggestion)

  @classmethod
  def apply_conditional_transformation_to_experiment(cls, experiment):
    conditionals = experiment.conditionals
    conditionals_as_cat_parameter_list = [cls.convert_conditional_to_categorical_parameter(c) for c in conditionals]
    unconditioned_parameter_list = []
    for parameter in experiment.parameters:
      parameter_dict = dataclass_to_dict(parameter)
      parameter_dict["conditions"] = {}
      unconditioned_parameter_list.append(parameter_dict)
    unconditioned_parameter_list.extend(conditionals_as_cat_parameter_list)
    return create_experiment_from_template(
      experiment_template=experiment,
      parameters=unconditioned_parameter_list,
      conditionals=[],
    )

  @classmethod
  def remove_conditional_transformation_from_suggestion(cls, original_experiment, unconditioned_suggestion):
    return LocalSuggestion(
      assignments=unconditioned_suggestion.get_assignments(original_experiment),
      task=unconditioned_suggestion.task,
    )

  @classmethod
  def form_domain_info(cls, experiment):
    constraint_list = []
    if experiment.linear_constraints:
      constraint_list = cls.parse_experiment_constraints_to_func_list(experiment)

    domain_components = [dict(zip(("var_type", "elements"), cls.pe_parameter_info(p))) for p in experiment.parameters]
    force_hitandrun_sampling = bool(experiment.linear_constraints)

    priors = None
    if any(p.prior for p in experiment.parameters):
      priors = [cls.parameter_to_prior_info(p) for p in experiment.parameters]

    return DomainInfo(
      constraint_list=constraint_list,
      domain_components=domain_components,
      force_hitandrun_sampling=force_hitandrun_sampling,
      priors=priors,
    )

  @classmethod
  def make_points_sampled(cls, experiment, observations):
    observation_count = len(observations)
    points = numpy.empty((observation_count, experiment.dimension))
    values = numpy.zeros((observation_count, experiment.num_metrics))
    value_vars = numpy.zeros((observation_count, experiment.num_metrics))
    failures = numpy.zeros(observation_count, dtype=bool)
    task_costs = numpy.ones(observation_count)
    for i, observation in enumerate(observations):
      points[i, :] = cls.get_point_from_assignments(experiment, observation.assignments)
      if not observation.failed:
        for j, metric in enumerate(experiment.metrics):
          metric_evaluation = observation.get_metric_evaluation_by_name(metric.name)
          values[i, j] = metric_evaluation.value
          if metric_evaluation.value_stddev:
            value_vars[i, j] = metric_evaluation.value_stddev

      failures[i] = observation.failed

      if experiment.is_multitask:
        assert observation.task
        task_costs[i] = observation.task.cost

    return PointsContainer(
      points=points,
      values=values,
      value_vars=value_vars,
      failures=failures,
      task_costs=task_costs if experiment.is_multitask else None,
    )

  @classmethod
  def multisolution_best_assignments(cls, experiment, observations):
    points_sampled = cls.make_points_sampled(experiment, observations)
    view_input = {
      "domain_info": cls.form_domain_info(experiment),
      "metrics_info": cls.form_basic_metric_info(experiment),
      "num_solutions": experiment.num_solutions,
      "points_sampled": points_sampled,
      "tag": {},
      "task_options": [t.cost for t in experiment.tasks],
    }
    response = MultisolutionBestAssignments(view_input).view()
    best_indices = [int(i) for i in response["best_indices"] if i is not None]
    return best_indices

  @classmethod
  def form_metrics_info(cls, experiment, points_sampled=None):
    metrics_info = cls.form_basic_metric_info(experiment)
    if experiment.num_solutions == 1:
      return metrics_info
    assert points_sampled is not None
    return cls.convert_metric_info_for_multisolution(metrics_info, points_sampled)

  @classmethod
  def convert_metric_info_for_multisolution(cls, metrics_info, points_sampled):
    optimized_metrics_index = metrics_info.optimized_metrics_index
    assert len(optimized_metrics_index) == 1
    optimized_index = optimized_metrics_index[0]
    multisolution_threshold = cls.compute_multisolution_threshold(
      metrics_info.objectives,
      points_sampled,
      optimized_index,
      MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
    )
    metrics_info.constraint_metrics_index.append(optimized_index)
    metrics_info.constraint_metrics_index.sort()
    metrics_info.optimized_metrics_index = []
    metrics_info.user_specified_thresholds[optimized_index] = multisolution_threshold
    return metrics_info

  @staticmethod
  def compute_multisolution_threshold(objectives, points_sampled, optimized_index, quantile_for_max):
    assert len(objectives) == points_sampled.values.shape[1]
    objective = objectives[optimized_index]
    points_sampled_values = points_sampled.values[~points_sampled.failures, optimized_index]
    assert len(points_sampled_values) > 0
    quantile = quantile_for_max if objective == "maximize" else (1 - quantile_for_max)
    # NOTE: Probably should be a function of the number of solutions but we will fix for now
    multisolution_threshold = numpy.quantile(points_sampled_values, quantile)
    return multisolution_threshold

  @staticmethod
  def form_basic_metric_info(experiment):
    objectives = []
    user_specified_thresholds = []
    optimized_metrics_index = []
    constraint_metrics_index = []
    for i, metric in enumerate(experiment.metrics):
      objectives.append(metric.objective)
      user_specified_thresholds.append(metric.threshold)
      if metric.is_optimized:
        optimized_metrics_index.append(i)
      elif metric.is_constraint:
        constraint_metrics_index.append(i)

    return MetricsInfo(
      requires_pareto_frontier_optimization=experiment.requires_pareto_frontier_optimization,
      observation_budget=experiment.observation_budget,
      user_specified_thresholds=user_specified_thresholds,
      objectives=objectives,
      optimized_metrics_index=optimized_metrics_index,
      constraint_metrics_index=constraint_metrics_index,
    )

  @staticmethod
  def pe_parameter_info(parameter):
    if parameter.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
      elements = list(range(1, len(parameter.categorical_values) + 1))
    elif parameter.grid:
      elements = parameter.grid
    else:
      elements = [parameter.bounds.min, parameter.bounds.max]
    var_type = parameter.type if not parameter.grid else QUANTIZED_EXPERIMENT_PARAMETER_NAME

    if parameter.transformation == ParameterTransformationNames.LOG:
      assert parameter.type == DOUBLE_EXPERIMENT_PARAMETER_NAME or parameter.grid
      elements = numpy.log10(elements).tolist()
    return var_type, elements

  @staticmethod
  def parameter_to_prior_info(parameter):
    if parameter.prior and parameter.prior.name == ParameterPriorNames.NORMAL:
      name = ParameterPriorNames.NORMAL
      params = {
        "mean": parameter.prior.mean,
        "scale": parameter.prior.scale,
      }
    elif parameter.prior and parameter.prior.name == ParameterPriorNames.BETA:
      name = ParameterPriorNames.BETA
      params = {
        "shape_a": parameter.prior.shape_a,
        "shape_b": parameter.prior.shape_b,
      }
    else:
      name = None
      params = None
    return {
      "name": name,
      "params": params,
    }

  @staticmethod
  def parse_experiment_constraints_to_func_list(experiment):
    constraint_list = []
    for constraint in experiment.linear_constraints:
      nonzero_coef_map = {a.name: a.weight for a in constraint.terms}
      constraint_vec = [0] * experiment.dimension
      var_type = None

      for index, p in enumerate(experiment.parameters):
        if p.name in nonzero_coef_map:
          constraint_vec[index] = nonzero_coef_map[p.name]
          assert p.type in (DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME)
          var_type = p.type

      sign = -1 if constraint.type == ConstraintType.less_than else 1
      weights = [sign * v for v in constraint_vec]
      rhs = sign * constraint.threshold
      constraint_list.append({"weights": weights, "rhs": rhs, "var_type": var_type})
    return constraint_list

  @staticmethod
  def make_assignments_from_point(experiment, point):
    parameters = experiment.parameters
    assignments = {}
    for assignment, parameter in zip(point, parameters):
      if parameter.transformation == ParameterTransformationNames.LOG:
        assignment = 10**assignment
      if parameter.type in (INT_EXPERIMENT_PARAMETER_NAME, CATEGORICAL_EXPERIMENT_PARAMETER_NAME):
        assignment = round(assignment)
      if parameter.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        assignment = next(cv.name for cv in parameter.categorical_values if cv.enum_index == assignment)
      assignments[parameter.name] = assignment
    return assignments

  @staticmethod
  def get_point_from_assignments(experiment, assignments):
    point = numpy.empty(experiment.dimension)
    for i, parameter in enumerate(experiment.parameters):
      parameter_value = assignments.get(parameter.name, None)
      if parameter_value is None:
        parameter_value = replacement_value_if_missing(parameter)
      if parameter.transformation == ParameterTransformationNames.LOG:
        parameter_value = numpy.log10(parameter_value)
      elif parameter.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        parameter_value = next(cv.enum_index for cv in parameter.categorical_values if cv.name == parameter_value)
      point[i] = parameter_value
    return point

  @staticmethod
  def convert_conditional_to_categorical_parameter(conditional):
    return dict(
      name=conditional.name,
      type=CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
      categorical_values=[dict(name=v.name, enum_index=v.enum_index) for v in conditional.values],
    )

  @staticmethod
  def get_task_by_cost(experiment, task_cost):
    return next(t for t in experiment.tasks if t.cost == task_cost)


class GPSource(BaseOptimizationSource):
  def __init__(self, experiment):
    super().__init__(experiment)
    self.hyperparameters = self.get_default_hyperparameters(self.experiment)

  def form_gp_model_info(self, observations, hyperparameters):
    correct_mean_type = "constant"
    if len(observations) < max(self.experiment.dimension, 2):
      correct_mean_type = "zero"
    mean_info = {
      "mean_type": correct_mean_type,
      "poly_indices": None,
    }
    return GPModelInfo(
      hyperparameters=hyperparameters,
      max_simultaneous_af_points=MAX_SIMULTANEOUS_AF_POINTS,
      nonzero_mean_info=mean_info,
      task_selection_strategy="a_priori" if self.experiment.is_multitask else None,
    )

  def update_hyperparameters(self, observations, hyperparameters):
    if hyperparameters is None:
      hyperparameters = self.hyperparameters
    view_input = {
      "domain_info": self.form_domain_info(self.experiment),
      "model_info": self.form_gp_model_info(observations, hyperparameters),
      "points_sampled": self.make_points_sampled(self.experiment, observations),
      "tag": {},
      "metrics_info": self.form_metrics_info(self.experiment),
      "task_options": [t.cost for t in self.experiment.tasks],
    }
    response = GpHyperOptMultimetricView(view_input).view()
    self.hyperparameters = response["hyperparameter_dict"]
    return self.hyperparameters

  def next_point(self, observations):
    assert self.hyperparameters is not None
    points_sampled = self.make_points_sampled(self.experiment, observations)
    view_input = {
      "domain_info": self.form_domain_info(self.experiment),
      "model_info": self.form_gp_model_info(observations, self.hyperparameters),
      "num_to_sample": 1,
      "parallelism": PARALLEL_CONSTANT_LIAR,
      "points_sampled": points_sampled,
      "points_being_sampled": EMPTY_POINTS_CONTAINER,
      "tag": {},
      "metrics_info": self.form_metrics_info(self.experiment, points_sampled),
      "task_options": [t.cost for t in self.experiment.tasks],
    }
    if self.experiment.is_search or self.experiment.is_multisolution:
      response = SearchNextPoints(view_input).view()
    else:
      response = GpNextPointsCategorical(view_input).view()

    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    task_cost = None
    if self.experiment.is_multitask:
      task_cost = response["task_costs"][0]

    return suggested_points[0], task_cost

  @classmethod
  def get_default_hyperparameters(cls, experiment):
    return [cls.default_hyperparameter_dict(experiment) for _ in range(experiment.num_metrics)]

  @classmethod
  def default_hyperparameter_dict(cls, experiment):
    return {
      "alpha": DEFAULT_HYPERPARAMETER_ALPHA,
      "length_scales": [[cls.default_lengthscales(p)] for p in experiment.parameters],
      "tikhonov": None,
      "task_length": DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE if experiment.is_multitask else None,
    }

  @staticmethod
  def default_lengthscales(parameter):
    if parameter.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
      return None
    if parameter.grid:
      return max(numpy.diff(parameter.grid))
    edge_length = parameter.bounds.max - parameter.bounds.min
    default = 0.1 * edge_length
    if parameter.type == INT_EXPERIMENT_PARAMETER_NAME:
      default = max(default, 0.5)
    return default


class SPESource(BaseOptimizationSource):
  def next_point(self, observations):
    points_sampled = self.make_points_sampled(self.experiment, observations[::-1])
    view_input = {
      "domain_info": self.form_domain_info(self.experiment),
      "num_to_sample": 1,
      "points_sampled": points_sampled,
      "points_being_sampled": EMPTY_POINTS_CONTAINER,
      "tag": {},
      "metrics_info": self.form_metrics_info(self.experiment, points_sampled),
      "task_options": [t.cost for t in self.experiment.tasks],
    }
    if self.experiment.is_search or self.experiment.is_multisolution:
      response = SPESearchNextPoints(view_input).view()
    else:
      response = SPENextPoints(view_input).view()
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]

    task_cost = None
    if self.experiment.is_multitask:
      task_cost = response["task_costs"][0]

    return suggested_points[0], task_cost


class RandomSearchSource(BaseOptimizationSource):
  def next_point(self, _):
    domain_info = self.form_domain_info(self.experiment)
    domain = CategoricalDomain(**asdict(domain_info))
    if domain_info.priors and not domain_info.constraint_list:
      samples = domain.generate_random_points_according_to_priors(1)
    else:
      samples = domain.generate_quasi_random_points_in_domain(1)

    task_cost = None
    if self.experiment.is_multitask:
      tasks_costs = [t.cost for t in self.experiment.tasks]
      task_cost = numpy.random.choice(tasks_costs)

    return samples[0], task_cost
