# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import sys

import numpy

from zigopt.common import *
from zigopt.assignments.model import MissingValueException, extract_array_for_computation_from_assignments
from zigopt.experiment.constant import METRIC_OBJECTIVE_TYPE_TO_NAME
from zigopt.experiment.constraints import parse_experiment_constraints_to_func_list
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import Prior
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.protobuf.lib import CopyFrom
from zigopt.services.base import Service
from zigopt.sigoptcompute.constant import (
  ACTIVATE_LINEAR_MEAN,
  DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OBSERVATIONS,
  DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OPEN_SUGGESTIONS,
  DEFAULT_CONSTRAINT_METRIC_QEI_RERANKING_MAX_OPEN_SUGGESTIONS,
  DEFAULT_NONZERO_MEAN,
  DEFAULT_QEI_RERANKING_MAX_OBSERVATIONS,
  DEFAULT_QEI_RERANKING_MAX_OPEN_SUGGESTIONS,
  DEFAULT_QEI_RERANKING_MAX_POINTS_TO_EVALUATE,
)
from zigopt.sigoptcompute.errors import SigoptComputeError
from zigopt.suggestion.unprocessed.model import SuggestionDataProxy

from libsigopt.aux.adapter_info_containers import DomainInfo, GPModelInfo, MetricsInfo, PointsContainer
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DEFAULT_TASK_SELECTION_STRATEGY,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MAX_SIMULTANEOUS_AF_POINTS,
  MINIMUM_VALUE_VAR,
  MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
  PARALLEL_CONSTANT_LIAR,
  PARALLEL_QEI,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)
from libsigopt.compute.views.rest.gp_ei_categorical import GpEiCategoricalView
from libsigopt.compute.views.rest.gp_hyper_opt_multimetric import GpHyperOptMultimetricView
from libsigopt.compute.views.rest.gp_next_points_categorical import GpNextPointsCategorical
from libsigopt.compute.views.rest.multisolution_best_assignments import MultisolutionBestAssignments
from libsigopt.compute.views.rest.search_next_points import SearchNextPoints
from libsigopt.compute.views.rest.spe_next_points import SPENextPoints
from libsigopt.compute.views.rest.spe_search_next_points import SPESearchNextPoints


#: Maximum ``num_to_sample`` (= ``q``) to request from libsigopt.compute when using the CL-max heuristic.
#: Reasons for limiting: cost and incremental gain
#: Cost: If C is the cost of obtaining 1 ``point_to_sample``, then to first-order,
#: CL-max with ``q`` points costs ``q * C``.
#: More accurately, 1 point costs ``C = O(dim * N^3)`` and ``q`` points costs
#: ``O(q * dim * (N + q)^3)`` where ``N`` is ``num_sampled``
#: Incremental gain: our experience and others' published results (e.g., Ginsbourger 2008)
#: indicate that CL methods provide almost no incremental benefit above 5-10 points.
MAXIMUM_NUMBER_OF_SUGGESTIONS_CL_MAX = 10


class SCAdapter(Service):
  def call_sigoptcompute(self, cls, view_input):
    try:
      return cls(view_input, logging_service=self.services.logging_service).call()
    except (ValueError, IndexError, numpy.linalg.LinAlgError) as e:
      points_sampled = view_input.get("points_sampled", None)
      num_points_sampled = 0 if points_sampled is None else len(points_sampled.points)
      logging_view_input = omit(view_input, "points_sampled")
      logging_view_input["num_points_sampled"] = num_points_sampled

      self.services.exception_logger.process_soft_exception(
        exc_info=sys.exc_info(),
        extra=dict(view_input=logging_view_input, libsigopt_compute_class=cls.__name__),
      )
      raise SigoptComputeError(e) from e

  """
  Translates requests from zigopt (containing Experiments, Suggestions, Observations, etc),
  to requests that sigoptcompute can understand (serialized numeric data).
  """
  # NOTE - This has been modified for metric constraint experiments to keep the next points call
  # under ~120 seconds in the worst case scenario.
  # This is designed for upward to 5 constraint metrics (with 1 optimized metric)
  def _use_qei_for_next_points(
    self,
    dimension,
    num_observations,
    num_open_suggestions,
    has_constraint_metrics,
    constraint_list,
  ):
    if has_constraint_metrics and not constraint_list:
      use_qei_for_next_points = self.services.config_broker.get(
        "features.useQeiForConstraintMetricsNextPoints",
        True,
      )
      return (
        use_qei_for_next_points
        and 0 < num_open_suggestions < DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OPEN_SUGGESTIONS
        and num_observations <= DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OBSERVATIONS
      )
    return False

  # NOTE - This is designed to keep the cost of reranking <100ms
  #     We maybe have more wiggle room, but I'm going to leave this for now and reinvestigate later
  #     Additionally, there's probably more work to be done on the computational speedup
  # NOTE - The reranking for experiments with constraint metrics is designed to keep the timing to <=350ms
  # This is designed for upward to 5 constraint metrics (with 1 optimized metric)
  def _use_qei_for_reranking(self, num_to_evaluate, num_observations, num_open_suggestions, has_constraint_metrics):
    max_points_to_evaluate = self.services.config_broker.get(
      "features.qeiRerankingMaxPointsToEvaluate",
      DEFAULT_QEI_RERANKING_MAX_POINTS_TO_EVALUATE,
    )
    max_observations = self.services.config_broker.get(
      "features.qeiRerankingMaxObservations",
      DEFAULT_QEI_RERANKING_MAX_OBSERVATIONS,
    )
    max_open_suggestions = self.services.config_broker.get(
      "features.qeiRerankingMaxOpenSuggestions",
      DEFAULT_QEI_RERANKING_MAX_OPEN_SUGGESTIONS,
    )
    if has_constraint_metrics:
      max_open_suggestions = DEFAULT_CONSTRAINT_METRIC_QEI_RERANKING_MAX_OPEN_SUGGESTIONS
    return (
      0 < num_open_suggestions < max_open_suggestions
      and num_observations <= max_observations
      and num_to_evaluate <= max_points_to_evaluate
    )

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
  def _convert_multisolution_into_search(metrics_info, points_sampled):
    optimized_metrics_index = metrics_info.optimized_metrics_index
    assert len(optimized_metrics_index) == 1
    optimized_index = optimized_metrics_index[0]
    multisolution_threshold = SCAdapter.compute_multisolution_threshold(
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
  def form_metrics_info(experiment):
    objectives = []
    user_specified_thresholds = []
    optimized_metrics_index = []
    constraint_metrics_index = []
    for i, metric in enumerate(experiment.all_metrics):
      objectives.append(METRIC_OBJECTIVE_TYPE_TO_NAME[metric.objective])
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
  def form_metrics_info_for_search_next_point(experiment, points_sampled):
    metrics_info = SCAdapter.form_metrics_info(experiment)
    if experiment.num_solutions == 1:
      return metrics_info  # this is a standard search experiment
    return SCAdapter._convert_multisolution_into_search(metrics_info, points_sampled)

  @staticmethod
  def form_gp_parallelism_strategy(use_qei):
    if use_qei:
      return PARALLEL_QEI
    return PARALLEL_CONSTANT_LIAR

  # TODO(RTL-108): Eventually move MC iterations info in here
  def form_gp_model_info(
    self,
    experiment,
    hyperparameter_dict,
    nonzero_mean_choice,
    num_successful_points,
  ):
    nonzero_mean_info = self._parse_nonzero_mean_choice(
      nonzero_mean_choice,
      num_successful_points,
      experiment.dimension,
    )
    max_simultaneous_af_points = self.services.config_broker.get(
      "model.max_simultaneous_af_points", default=MAX_SIMULTANEOUS_AF_POINTS
    )

    return GPModelInfo(
      hyperparameters=hyperparameter_dict,
      max_simultaneous_af_points=max_simultaneous_af_points,
      nonzero_mean_info=nonzero_mean_info,
      task_selection_strategy=DEFAULT_TASK_SELECTION_STRATEGY if experiment.is_multitask else None,
    )

  def multisolution_best_assignments(
    self,
    experiment,
    observations,
    tag=None,
  ):
    assert observations
    points_sampled = self._make_points_sampled(experiment, observations, len(observations))
    view_input = {
      "domain_info": self.generate_domain_info(experiment),
      "metrics_info": self.form_metrics_info(experiment),
      "num_solutions": experiment.num_solutions,
      "points_sampled": points_sampled,
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "task_options": [t.cost for t in experiment.tasks],
    }
    response = self.call_sigoptcompute(MultisolutionBestAssignments, view_input)
    best_indices = [int(i) for i in response["best_indices"] if i is not None]
    return best_indices

  def random_search_next_points(
    self,
    experiment,
    num_to_suggest,
    tag=None,
  ):
    view_input = {
      "domain_info": self.generate_domain_info(experiment, only_active_categorical_values=True),
      "num_to_sample": num_to_suggest,
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
    }
    response = self.call_sigoptcompute(RandomSearchNextPoints, view_input)
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    return self._make_suggestion_datas(experiment, suggested_points)

  def gp_ei_categorical(
    self,
    experiment,
    observations,
    hyperparameter_dict,
    suggestion_datas_to_evaluate,
    open_suggestion_datas=None,
    nonzero_mean_choice=None,
    tag=None,
  ):
    assert not experiment.conditionals
    if not suggestion_datas_to_evaluate:
      return []
    assert observations

    points_sampled = self._make_points_sampled(experiment, observations, len(observations))
    failure_count = numpy.sum(points_sampled.failures)
    num_successful_points = int(len(observations) - failure_count)

    model_info = self.form_gp_model_info(
      experiment,
      hyperparameter_dict,
      nonzero_mean_choice,
      num_successful_points,
    )
    parallelism = self.form_gp_parallelism_strategy(
      self._use_qei_for_reranking(
        len(suggestion_datas_to_evaluate),
        len(observations),
        len(open_suggestion_datas) if open_suggestion_datas else 0,
        experiment.has_constraint_metrics,
      )
    )

    view_input = {
      "domain_info": self.generate_domain_info(experiment),
      "model_info": model_info,
      "parallelism": parallelism,
      "points_sampled": points_sampled,
      "points_to_evaluate": self._make_points_to_evaluate(experiment, suggestion_datas_to_evaluate),
      "points_being_sampled": self._make_points_being_sampled(experiment, open_suggestion_datas),
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info(experiment),
      "task_options": [t.cost for t in experiment.tasks],
    }
    response = self.call_sigoptcompute(GpEiCategoricalView, view_input)
    return [float(ei) for ei in response["expected_improvement"]]

  def spe_next_points(
    self,
    experiment,
    observation_iterator,
    num_to_suggest,
    observation_count,
    open_suggestion_datas=None,
    tag=None,
  ):
    points_sampled = self._make_points_sampled(experiment, observation_iterator, observation_count)
    view_input = {
      "domain_info": self.generate_domain_info(experiment),
      "num_to_sample": num_to_suggest,
      "points_being_sampled": self._make_points_being_sampled(experiment, open_suggestion_datas),
      "points_sampled": points_sampled,
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info(experiment),
      "task_options": [t.cost for t in experiment.tasks],
    }

    response = self.call_sigoptcompute(SPENextPoints, view_input)
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    task_costs = (float(cost) for cost in response["task_costs"]) if experiment.is_multitask else None

    if len(suggested_points) < num_to_suggest:
      self.services.exception_logger.soft_exception(
        "SPE failed to generate enough suggestions",
        extra=dict(
          count_suggested_points=len(suggested_points),
          num_to_suggest=num_to_suggest,
          view_input=view_input,
        ),
      )

    return self._make_suggestion_datas(experiment, suggested_points, task_costs)

  def spe_search_next_points(
    self,
    experiment,
    observation_iterator,
    num_to_suggest,
    observation_count,
    open_suggestion_datas=None,
    tag=None,
  ):
    points_sampled = self._make_points_sampled(experiment, observation_iterator, observation_count)
    view_input = {
      "domain_info": self.generate_domain_info(experiment),
      "num_to_sample": num_to_suggest,
      "points_being_sampled": self._make_points_being_sampled(experiment, open_suggestion_datas),
      "points_sampled": points_sampled,
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info_for_search_next_point(experiment, points_sampled),
      "task_options": [t.cost for t in experiment.tasks],
    }

    assert view_input["metrics_info"].optimized_metrics_index == []
    assert not view_input["metrics_info"].has_optimization_metrics

    response = self.call_sigoptcompute(SPESearchNextPoints, view_input)
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    task_costs = None

    if len(suggested_points) < num_to_suggest:
      self.services.exception_logger.soft_exception(
        "SPE Search failed to generate enough suggestions",
        extra=dict(
          count_suggested_points=len(suggested_points),
          num_to_suggest=num_to_suggest,
          view_input=view_input,
        ),
      )

    return self._make_suggestion_datas(experiment, suggested_points, task_costs)

  def gp_next_points_categorical(
    self,
    experiment,
    observations,
    hyperparameter_dict,
    num_to_suggest,
    open_suggestion_datas=None,
    nonzero_mean_choice=None,
    tag=None,
  ):
    if not observations:
      return self._make_suggestion_datas(experiment, [])
    assert 1 <= num_to_suggest <= MAXIMUM_NUMBER_OF_SUGGESTIONS_CL_MAX
    assert not experiment.conditionals

    points_sampled = self._make_points_sampled(experiment, observations, len(observations))
    failure_count = numpy.sum(points_sampled.failures)
    num_successful_points = int(len(observations) - failure_count)

    domain_info = self.generate_domain_info(experiment)
    model_info = self.form_gp_model_info(
      experiment,
      hyperparameter_dict,
      nonzero_mean_choice,
      num_successful_points,
    )
    parallelism = self.form_gp_parallelism_strategy(
      self._use_qei_for_next_points(
        experiment.dimension,
        len(observations),
        len(open_suggestion_datas) if open_suggestion_datas else 0,
        experiment.has_constraint_metrics,
        domain_info.constraint_list,
      )
    )

    view_input = {
      "domain_info": domain_info,
      "model_info": model_info,
      "num_to_sample": num_to_suggest,
      "parallelism": parallelism,
      "points_sampled": points_sampled,
      "points_being_sampled": self._make_points_being_sampled(experiment, open_suggestion_datas),
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info(experiment),
      "task_options": [t.cost for t in experiment.tasks],
    }

    response = self.call_sigoptcompute(GpNextPointsCategorical, view_input)
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    task_costs = (float(cost) for cost in response["task_costs"]) if experiment.is_multitask else None

    if len(suggested_points) < num_to_suggest:
      self.services.exception_logger.soft_exception(
        "GP failed to generate enough suggestions",
        extra=dict(
          count_suggested_points=len(suggested_points),
          num_to_suggest=num_to_suggest,
          view_input=view_input,
        ),
      )

    return self._make_suggestion_datas(experiment, suggested_points, task_costs)

  def search_next_points(
    self,
    experiment,
    observations,
    hyperparameter_dict,
    num_to_suggest,
    open_suggestion_datas=None,
    nonzero_mean_choice=None,
    tag=None,
  ):
    if not observations:
      return self._make_suggestion_datas(experiment, [])
    assert 1 <= num_to_suggest <= MAXIMUM_NUMBER_OF_SUGGESTIONS_CL_MAX
    assert experiment.is_search or experiment.num_solutions > 1

    points_sampled = self._make_points_sampled(experiment, observations, len(observations))
    failure_count = numpy.sum(points_sampled.failures)
    num_successful_points = int(len(observations) - failure_count)

    model_info = self.form_gp_model_info(
      experiment,
      hyperparameter_dict,
      nonzero_mean_choice,
      num_successful_points,
    )

    view_input = {
      "domain_info": self.generate_domain_info(experiment),
      "model_info": model_info,
      "num_to_sample": num_to_suggest,
      "parallelism": self.form_gp_parallelism_strategy(use_qei=False),
      "points_sampled": points_sampled,
      "points_being_sampled": self._make_points_being_sampled(experiment, open_suggestion_datas),
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info_for_search_next_point(experiment, points_sampled),
      "task_options": [t.cost for t in experiment.tasks],
    }

    assert view_input["metrics_info"].optimized_metrics_index == []
    assert not view_input["metrics_info"].has_optimization_metrics

    response = self.call_sigoptcompute(SearchNextPoints, view_input)
    suggested_points = [[float(coord) for coord in point] for point in response["points_to_sample"]]
    task_costs = None

    if len(suggested_points) < num_to_suggest:
      self.services.exception_logger.soft_exception(
        "Search failed to generate enough suggestions",
        extra=dict(
          count_suggested_points=len(suggested_points),
          num_to_suggest=num_to_suggest,
          view_input=view_input,
        ),
      )

    return self._make_suggestion_datas(experiment, suggested_points, task_costs)

  # TODO(RTL-109): Think on if this function would be better placed inside OptimizationSource
  @staticmethod
  @generator_to_list
  def _make_suggestion_datas(experiment, suggested_points, task_costs=None):
    parameters = experiment.all_parameters_sorted
    task_costs = task_costs or [None] * len(suggested_points)

    for suggested_point, task_cost in zip(suggested_points, task_costs):
      data = SuggestionData()
      for assignment, parameter in zip(suggested_point, parameters):
        if parameter.has_log_transformation:
          assignment = 10**assignment
        if parameter.is_integer or parameter.is_categorical:
          assignment = round(assignment)
        data.assignments_map[parameter.name] = assignment
      if task_cost is not None:
        CopyFrom(data.task, experiment.get_task_by_cost(task_cost).copy_protobuf())

      yield SuggestionDataProxy(data)

  def gp_hyper_opt_categorical(
    self,
    experiment,
    observations,
    old_hyperparameter_dict,
    nonzero_mean_choice=None,
    tag=None,
  ):
    assert not experiment.conditionals
    assert observations

    points_sampled = self._make_points_sampled(experiment, observations, len(observations))
    failure_count = numpy.sum(points_sampled.failures)
    num_successful_points = int(len(observations) - failure_count)
    domain_info = self.generate_domain_info(experiment)

    model_info = self.form_gp_model_info(
      experiment,
      old_hyperparameter_dict,
      nonzero_mean_choice,
      num_successful_points,
    )

    view_input = {
      "domain_info": domain_info,
      "model_info": model_info,
      "points_sampled": points_sampled,
      "tag": self.supplement_tag_with_experiment_id(tag, experiment),
      "metrics_info": self.form_metrics_info(experiment),
      "task_options": [t.cost for t in experiment.tasks],
    }

    response = self.call_sigoptcompute(GpHyperOptMultimetricView, view_input)
    return response["hyperparameter_dict"]

  @staticmethod
  def generate_domain_info(experiment, only_active_categorical_values=False):
    def pe_parameter_info(p):
      name = p.name
      if p.is_categorical:
        var_type = CATEGORICAL_EXPERIMENT_PARAMETER_NAME
        categorical_values = p.active_categorical_values if only_active_categorical_values else p.all_categorical_values
        elements = [c.enum_index for c in categorical_values]
      elif p.is_grid:
        var_type = QUANTIZED_EXPERIMENT_PARAMETER_NAME
        elements = p.grid_values
        if p.has_log_transformation:
          elements = numpy.log10(elements).tolist()
      else:
        if p.is_double:
          var_type = DOUBLE_EXPERIMENT_PARAMETER_NAME
          elements = [p.bounds.minimum, p.bounds.maximum]
          if p.has_log_transformation:
            elements = numpy.log10(elements).tolist()
        else:
          var_type = INT_EXPERIMENT_PARAMETER_NAME
          elements = [p.bounds.minimum, p.bounds.maximum]
      return var_type, elements, name

    def parameter_to_prior_info(p):
      prior_type = p.prior.GetFieldOrNone("prior_type")
      if prior_type == Prior.NORMAL:
        assert p.is_double
        name = ParameterPriorNames.NORMAL
        params = {
          "mean": p.prior.normal_prior.mean,
          "scale": p.prior.normal_prior.scale,
        }
      elif prior_type == Prior.BETA:
        assert p.is_double
        name = ParameterPriorNames.BETA
        params = {
          "shape_a": p.prior.beta_prior.shape_a,
          "shape_b": p.prior.beta_prior.shape_b,
        }
      else:
        name = None
        params = None
      return {
        "name": name,
        "params": params,
      }

    return DomainInfo(
      constraint_list=parse_experiment_constraints_to_func_list(experiment),
      domain_components=[
        dict(zip(("var_type", "elements", "name"), pe_parameter_info(p))) for p in experiment.all_parameters_sorted
      ],
      force_hitandrun_sampling=experiment.force_hitandrun_sampling,
      priors=[parameter_to_prior_info(p) for p in experiment.all_parameters_sorted] if experiment.has_prior else None,
    )

  @staticmethod
  def _make_points_sampled(
    experiment,
    observations,
    observation_count,
  ):
    parameters = [p.copy_protobuf() for p in experiment.all_parameters]

    points = numpy.empty((observation_count, experiment.dimension))
    values = numpy.zeros((observation_count, len(experiment.all_metrics)))
    value_vars = numpy.ones((observation_count, len(experiment.all_metrics)))
    failures = numpy.zeros(observation_count, dtype=bool)
    task_costs = numpy.ones(observation_count)
    k = 0
    for k, observation in enumerate(observations):
      observation_data = observation.data
      try:
        extract_array_for_computation_from_assignments(observation_data, parameters, points[k, :])
      except MissingValueException as e:
        raise MissingValueException(f"{str(e)} - experiment {experiment.id}") from e
      values[k, :] = observation_data.sorted_all_metric_values(experiment)
      failures[k] = bool(observation_data.reported_failure)
      task_costs[k] = observation_data.task.cost

      value_var = observation_data.sorted_all_metric_value_vars(experiment)
      if value_var is None or any(numpy.isnan(value_var)):
        value_var = [MINIMUM_VALUE_VAR] * len(experiment.all_metrics)
      value_vars[k, :] = numpy.fmax(value_var, MINIMUM_VALUE_VAR)
    assert observation_count == k + 1

    return PointsContainer(
      points=points,
      values=values,
      value_vars=value_vars,
      failures=failures,
      task_costs=task_costs if experiment.is_multitask else None,
    )

  # TODO(RTL-110): Is there a reason/benefit to passing these as proxies?  Or casting them as proxies inside?
  @staticmethod
  def _make_points_being_sampled(experiment, open_suggestion_datas=None):
    open_suggestion_datas = open_suggestion_datas or []
    parameters = [p.copy_protobuf() for p in experiment.all_parameters]

    points = numpy.empty((len(open_suggestion_datas), experiment.dimension))
    task_costs = numpy.empty(len(open_suggestion_datas))
    for k, open_suggestion_data in enumerate(open_suggestion_datas):
      try:
        extract_array_for_computation_from_assignments(open_suggestion_data, parameters, points[k, :])
      except MissingValueException as e:
        raise MissingValueException(f"{str(e)} - experiment {experiment.id}") from e
      task_costs[k] = open_suggestion_data.task.cost

    return PointsContainer(
      points=points,
      task_costs=task_costs if experiment.is_multitask else None,
    )

  _make_points_to_evaluate = _make_points_being_sampled

  @staticmethod
  def supplement_tag_with_experiment_id(tag, experiment):
    tag = coalesce(tag, {})
    assert is_mapping(tag)
    tag["experiment_id"] = experiment.id
    return tag

  def _parse_nonzero_mean_choice(self, nonzero_mean_choice, num_points, dimension):
    """Interpret user choice of nonzero mean for GP

        If the value None is passed, SigOpt engages its default.  Right now, that means a zero mean,
        but that is changing soon to something more complicated.
        Otherwise we provide different options for the user to explain their choices within a dictionary.  The
        dictionary must always have two items in it:
          mean_type: one of ('zero','constant','linear','custom')
          poly_indices: a list of lists which describes the polynomial to be used.

        These three options are provided for simplicity, so that the most common nonzero means
        can be constructed within sigoptcompute rather than requiring an understanding here in zigopt.

        Option 1) Pass one of 'zero', 'constant', 'linear' for mean_type and None for poly_indices.
          This will allow sigoptcompute to figure out the appropriate indices.
        Option 2) Pass 'custom' for mean type and a list of lists of nonnegative integers for poly_indices
          This will allow sigoptcompute to receive custom chosen indices.
          Example: In 3D if you wanted 1 + x^2 + xyz + yz^3 you use poly_indices=[[0,0,0], [2,0,0], [1,1,1], [0,1,3]]
        Option 3) Pass 'automatic' for mean_type and None for poly_indices.
          This will cause sigoptcompute to automatically choose a (hopefully) good mean based on its logic.

        The 'automatic' option (Option 3) will choose 'zero', 'constant' or 'linear' based on the
        number of points that have been sampled.  This logic is subject to change as we evolve SCAdapter
        and Qworker and sigoptcompute itself.

        :param nonzero_mean_choice: Used to determine what mean to command sigoptcompute to use
        :type nonzero_mean_choice: One of the options above
        :param num_points: number of points of historical data
        :type num_points: int >=0  (Could 0 actually happen?)
        :param dimension: number of dimensions for this data
        :type dimension: int >1
        :return nonzero_mean_info: dict for json to interpret and send to libsigopt.compute
        :rtype nonzero_mean_info: dict
        """
    if nonzero_mean_choice is None:
      nonzero_mean_default = self.services.config_broker.get("model.nonzero_mean_default", default=DEFAULT_NONZERO_MEAN)
      nonzero_mean_choice = {"mean_type": nonzero_mean_default, "poly_indices": None}

    if is_mapping(nonzero_mean_choice):
      if not all(mean_keys in nonzero_mean_choice for mean_keys in ("mean_type", "poly_indices")):
        raise ValueError('"mean_type" and "poly_indices" are required in nonzero_mean_choice')
      passed_mean_type = nonzero_mean_choice.get("mean_type")
      passed_poly_indices = nonzero_mean_choice.get("poly_indices")
      if passed_mean_type is None:
        raise ValueError("You must choose a mean_type in nonzero_mean_choice")
      elif not is_string(passed_mean_type):
        raise ValueError(f"mean_type should be a string, but passed: {type(passed_mean_type)}")
      elif not (passed_poly_indices is None or is_sequence(passed_poly_indices)):
        raise ValueError("poly_indices must be a list of lists, or None to let sigoptcompute choose")
      else:
        if passed_mean_type == "custom":
          if passed_poly_indices is None:
            raise ValueError("You must choose indices if you want a custom mean")
          else:
            correct_mean_type = passed_mean_type
            correct_poly_indices = passed_poly_indices
        elif passed_mean_type == "automatic":
          if passed_poly_indices is not None:
            raise ValueError("When requesting automatic indices construction, poly_indices must be None")
          else:
            if num_points < max(dimension, 2):
              correct_mean_type = "zero"
            elif num_points < 3 * dimension:
              correct_mean_type = "constant"
            else:
              correct_mean_type = "linear" if ACTIVATE_LINEAR_MEAN else "constant"
            correct_poly_indices = None
        elif passed_mean_type in ("zero", "constant", "linear"):
          if passed_poly_indices is not None:
            raise ValueError(f"Mean is chosen by mean_type={passed_mean_type} ... poly_indices should be None")
          else:
            correct_mean_type = passed_mean_type
            correct_poly_indices = None
        else:
          raise ValueError(f"Unrecognized mean_type, {passed_mean_type}")
    else:
      raise TypeError(f"nonzero_mean_choice should be a dictionary, but is {type(nonzero_mean_choice)}")

    return {
      "mean_type": correct_mean_type,
      "poly_indices": correct_poly_indices,
    }
