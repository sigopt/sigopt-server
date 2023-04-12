# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication, client_token_authentication
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.common.struct import ImmutableStruct
from zigopt.conditionals.from_json import set_experiment_conditionals_list_from_json
from zigopt.experiment.constant import (
  ALL_METRIC_OBJECTIVE_NAMES,
  ALL_METRIC_STRATEGY_NAMES,
  EXPERIMENT_NAME_TO_TYPE,
  MAX_CONSTRAINT_METRICS,
  MAX_METRICS_ANY_STRATEGY,
  MAX_OPTIMIZED_METRICS,
  MetricStrategyNames,
)
from zigopt.experiment.model import Experiment, ExperimentMetaProxy
from zigopt.experiment.util import group_metric_strategies_from_json, source_class_from_experiment_meta
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.experiments.base import get_budget_key, get_budget_param
from zigopt.handlers.validate.experiment import (
  validate_experiment_json_dict_for_create,
  validate_experiment_name,
  validate_metric_name,
  validate_metric_objective,
  validate_metric_strategy,
  validate_variable_name,
)
from zigopt.handlers.validate.metadata import validate_client_provided_data
from zigopt.handlers.validate.validate_dict import (
  ValidationType,
  get_opt_with_validation,
  get_with_validation,
  key_present,
)
from zigopt.json.builder import ExperimentJsonBuilder
from zigopt.net.errors import BadParamError
from zigopt.parameters.from_json import set_experiment_parameter_list_from_json
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentConstraint,
  ExperimentMeta,
  ExperimentMetric,
  ExperimentParameter,
  Task,
  Term,
)
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.suggestion.sampler.grid import GridSampler

from libsigopt.aux.constant import MAX_NUM_INT_CONSTRAINT_VARIABLES
from libsigopt.aux.errors import InvalidValueError, MissingJsonKeyError


class BaseExperimentsCreateHandler(Handler):
  allow_development = True
  JsonBuilder = ExperimentJsonBuilder
  user_facing_class_name = "Experiment"

  Params = ImmutableStruct(
    "ExperimentCreateParams",
    (
      "client",
      "meta",
      "name",
      "project",
    ),
  )

  def get_client(self):
    raise NotImplementedError()

  @classmethod
  def validate_json_params(cls, data):
    validate_experiment_json_dict_for_create(data)

  def parse_validated_params(self, data):
    experiment_name = validate_experiment_name(get_with_validation(data, "name", ValidationType.string))
    experiment_type_string = get_opt_with_validation(data, "type", ValidationType.string)
    client = self.get_client()
    project = self.get_project(data)
    experiment_meta = self.make_experiment_meta_from_json(
      data,
      experiment_type_string,
      self.auth.development,
    )
    return self.Params(
      client=client,
      meta=experiment_meta,
      name=experiment_name,
      project=project,
    )

  def parse_params(self, request):
    data = request.params()
    self.validate_json_params(data)
    return self.parse_validated_params(data)

  def handle(self, params):
    experiment_name = params.name
    project = params.project
    client = params.client

    experiment_meta = params.meta

    if experiment_meta.runs_only and project is None:
      raise BadParamError(f"{self.user_facing_class_name}s must be placed in a project by defining the `project` field")

    now = current_datetime()
    experiment = Experiment(
      client_id=client.id,
      project_id=project and project.id,
      name=experiment_name,
      experiment_meta=experiment_meta,
      date_created=now,
      date_updated=now,
      created_by=(self.auth.current_user and self.auth.current_user.id),
    )
    self.services.experiment_service.verify_experiment_acceptability(
      self.auth,
      experiment,
      client,
    )

    if experiment.constraints:
      self.services.experiment_service.set_hitandrun_flag_using_rejection_sampling(experiment)

    self.services.experiment_service.insert(experiment)

    self._supplemental_db_insertions_after_experiment_insertion(experiment)
    self.services.experiment_service.incr_count_by_organization_id_for_billing(
      experiment,
      client.organization_id,
    )

    progress = self.services.experiment_progress_service.empty_progress(experiment)
    return self.JsonBuilder(experiment, progress_builder=progress.json_builder(), project=project)

  def get_project(self, data, default=None):
    if "project" in data:
      reference_id = get_opt_with_validation(data, "project", ValidationType.id_string)
      if reference_id is None:
        return None
      client = self.get_client()
      project = self.services.project_service.find_by_client_and_reference_id(
        client_id=client.id,
        reference_id=reference_id,
      )
      if project is None:
        raise BadParamError(f"Could not assign to project `{reference_id}`, the project does not exist.")
      return project
    return default

  def _supplemental_db_insertions_after_experiment_insertion(self, experiment):
    self._initialize_hyperparameters_as_necessary(experiment)

  # NOTE: Maybe this should cycle through all possible sources and check which ones need initialization?
  def _initialize_hyperparameters_as_necessary(self, experiment):
    base_source = source_class_from_experiment_meta(
      experiment.experiment_meta,
    )(self.services, experiment)
    base_source.construct_initial_hyperparameters()

  @classmethod
  def get_runs_only(cls, json_dict):
    return get_opt_with_validation(json_dict, "runs_only", ValidationType.boolean) or False

  @classmethod
  def get_budget_key_and_value(cls, json_dict, runs_only):
    try:
      budget, budget_key = get_budget_param(json_dict, runs_only, return_key=True)
    except MissingJsonKeyError:
      budget = None
      budget_key = get_budget_key(runs_only)
    return budget_key, budget

  @classmethod
  def make_experiment_meta_from_json(
    cls,
    json_dict,
    experiment_type_string,
    development,
  ):
    # pylint: disable=too-many-locals,too-many-statements
    if experiment_type_string is None:
      experiment_type = ExperimentMeta.OFFLINE
    else:
      experiment_type = EXPERIMENT_NAME_TO_TYPE.get(experiment_type_string)
      if experiment_type is None:
        raise BadParamError(f"Invalid experiment type: {experiment_type_string}")

    experiment_meta = ExperimentMeta()
    experiment_meta.experiment_type = experiment_type
    experiment_meta.development = development
    experiment_meta.runs_only = cls.get_runs_only(json_dict)
    set_experiment_conditionals_list_from_json(experiment_meta, json_dict)
    set_experiment_parameter_list_from_json(experiment_meta, json_dict, cls.user_facing_class_name)

    constraints = cls.get_constraints_from_json(
      json_dict,
      experiment_meta.all_parameters_unsorted,
    )
    experiment_meta.constraints.extend(constraints)

    all_metrics = cls.get_metric_list_from_json(json_dict)
    experiment_meta.metrics.extend(all_metrics)
    optimized_metrics = [m for m in experiment_meta.metrics if m.strategy == ExperimentMetric.OPTIMIZE]
    has_constraint_metrics = any(m.strategy == ExperimentMetric.CONSTRAINT for m in experiment_meta.metrics)
    has_optimization_metrics = len(optimized_metrics) > 0

    num_solutions = cls.get_num_solutions_from_json(
      json_dict,
      experiment_meta.all_parameters_unsorted,
    )
    experiment_meta.SetFieldIfNotNone("num_solutions", num_solutions)  # pylint: disable=protobuf-undefined-attribute

    parallel_bandwidth = cls.get_parallel_bandwidth_from_json(json_dict)
    experiment_meta.SetFieldIfNotNone(  # pylint: disable=protobuf-undefined-attribute
      "parallel_bandwidth", parallel_bandwidth
    )

    # Set observation budget if present and check to see which features require a budget
    budget_key, budget = cls.get_budget_key_and_value(json_dict, experiment_meta.runs_only)

    if experiment_type == ExperimentMeta.GRID:
      if len(experiment_meta.conditionals) > 0:
        raise BadParamError("Grid search experiments do not support conditional parameters currently.")
      experiment_meta.observation_budget = GridSampler.observation_budget_from_experiment_meta(experiment_meta)
      if budget is not None and budget != experiment_meta.observation_budget:
        raise BadParamError(
          f"The specified `{budget_key}` of {budget}"
          f" does not match the computed budget of {experiment_meta.observation_budget}"
        )
    elif budget is None:
      if len(optimized_metrics) > 1:
        raise BadParamError(f"{budget_key} is required for an experiment with more than one optimized metric")
      if has_constraint_metrics:
        raise BadParamError(f"{budget_key} is required for an experiment with constraint metrics")
      if num_solutions and num_solutions > 1:
        raise BadParamError(f"{budget_key} is required for an experiment with more than one solution")
    else:
      experiment_meta.observation_budget = budget

    # Check feature viability with conditionals
    if len(experiment_meta.conditionals) > 0:
      if num_solutions and num_solutions > 1:
        raise BadParamError("Conditional experiments cannot be run with multisolution experiments")

    # Check feature viability with multisolution experiments
    if num_solutions and num_solutions > 1:
      if num_solutions > experiment_meta.observation_budget:
        raise BadParamError("Observation budget needs to be larger than the number of solutions")
      if len(optimized_metrics) != 1:
        raise BadParamError("Multisolution experiments require exactly one optimized metric")

    client_provided_data = cls.get_client_provided_data(json_dict)
    experiment_meta.SetFieldIfNotNone(  # pylint: disable=protobuf-undefined-attribute
      "client_provided_data", client_provided_data
    )

    if not (has_optimization_metrics or has_constraint_metrics):
      raise BadParamError(f"{cls.user_facing_class_name}s must have optimized or constraint metrics")

    tasks = cls.get_tasks_from_json(json_dict)
    if tasks:
      if not budget:
        raise BadParamError(f"{budget_key} is required for an experiment with tasks (multitask)")
      if len(optimized_metrics) > 1:
        raise BadParamError(f"{cls.user_facing_class_name}s cannot have both tasks and multiple optimized metrics")
      if has_constraint_metrics:
        raise BadParamError(f"{cls.user_facing_class_name}s cannot have both tasks and constraint metrics")
      if num_solutions and num_solutions > 1:
        raise BadParamError(f"Multisolution {cls.user_facing_class_name} cannot be multitask")

      experiment_meta.tasks.extend(tasks)

    return ExperimentMetaProxy(experiment_meta)

  @classmethod
  def get_client_provided_data(cls, json_dict, default=None):
    if "metadata" not in json_dict:
      return default
    client_provided_data = get_opt_with_validation(json_dict, "metadata", ValidationType.object)
    return validate_client_provided_data(client_provided_data)

  @classmethod
  def get_metric_objective(cls, metric):
    objective = get_opt_with_validation(metric, "objective", ValidationType.string)
    if key_present(metric, "objective"):
      if objective is None:
        raise BadParamError(f"Objective field, if specified, must be one of {tuple(ALL_METRIC_OBJECTIVE_NAMES)}")
    objective = validate_metric_objective(objective)
    return objective

  @classmethod
  def get_metric_name(cls, metric, seen_names, num_metrics):
    name = get_opt_with_validation(metric, "name", ValidationType.string)
    if name is None and num_metrics > 1:
      raise BadParamError("Multimetric experiments do not support unnamed metrics")
    if name in seen_names:
      raise InvalidValueError(f"Duplicate metric name: {name}")
    return name

  @classmethod
  def get_metric_threshold(cls, metric, num_optimized_metrics, metric_strategy):
    threshold = get_opt_with_validation(metric, "threshold", ValidationType.number)
    metric_strategy = coalesce(metric_strategy, ExperimentMetric.OPTIMIZE)
    has_threshold_field_and_valid_value = key_present(metric, "threshold") and threshold is not None
    if metric_strategy == ExperimentMetric.OPTIMIZE:
      if num_optimized_metrics == 1 and has_threshold_field_and_valid_value:
        raise BadParamError(
          "Thresholds are only supported for experiments with more than one optimized metric."
          " Try an All-Constraint experiment instead by setting `strategy` to `constraint`."
        )
    elif metric_strategy == ExperimentMetric.CONSTRAINT:
      if not has_threshold_field_and_valid_value:
        raise BadParamError("Constraint metrics must have the threshold field defined")
    else:  # metric_strategy == ExperimentMetric.STORE
      if has_threshold_field_and_valid_value:
        raise BadParamError("Thresholds cannot be specified on stored metrics")

    return threshold

  @classmethod
  def get_metric_strategy(cls, metric):
    metric_strategy = get_opt_with_validation(metric, "strategy", ValidationType.string)
    if key_present(metric, "strategy"):
      if metric_strategy is None:
        raise BadParamError(f"Metric strategy field, if specified, must be one of {tuple(ALL_METRIC_STRATEGY_NAMES)}")
    metric_strategy = validate_metric_strategy(metric_strategy)
    return metric_strategy

  @classmethod
  def get_metric_list_from_json(cls, json_dict):
    metrics = get_opt_with_validation(
      json_dict,
      "metrics",
      ValidationType.arrayOf(ValidationType.oneOf([ValidationType.string, ValidationType.object])),
    )
    if metrics is None:
      assert MAX_METRICS_ANY_STRATEGY >= 1
      assert MAX_OPTIMIZED_METRICS >= 1
      return [ExperimentMetric()]
    if not metrics:
      raise BadParamError("The `metrics` list must contain a metric")
    if len(metrics) > MAX_METRICS_ANY_STRATEGY:
      raise BadParamError(f"Cannot have more then {MAX_METRICS_ANY_STRATEGY} metrics")
    strategy_to_metrics_map = group_metric_strategies_from_json(metrics)
    optimized_metrics = strategy_to_metrics_map.get(MetricStrategyNames.OPTIMIZE, [])
    if len(optimized_metrics) > MAX_OPTIMIZED_METRICS:
      raise BadParamError(f"{cls.user_facing_class_name}s must have at most {MAX_OPTIMIZED_METRICS} optimized metrics")
    constraint_metrics = strategy_to_metrics_map.get(MetricStrategyNames.CONSTRAINT, [])
    if len(constraint_metrics) > MAX_CONSTRAINT_METRICS:
      raise BadParamError(
        f"{cls.user_facing_class_name}s must have at most {MAX_CONSTRAINT_METRICS} constraint metrics"
      )
    seen_names = []
    metric_list = []
    for metric in metrics:
      if is_string(metric):
        name = metric
        objective = None
        threshold = None
        metric_strategy = None
      else:
        name = cls.get_metric_name(
          metric=metric,
          seen_names=seen_names,
          num_metrics=len(metrics),
        )
        objective = cls.get_metric_objective(metric=metric)
        metric_strategy = cls.get_metric_strategy(
          metric=metric,
        )
        threshold = cls.get_metric_threshold(
          metric=metric,
          num_optimized_metrics=len(optimized_metrics),
          metric_strategy=metric_strategy,
        )
      seen_names.append(name)
      name = napply(name, validate_metric_name)
      new_metric = ExperimentMetric(
        name=name,
        objective=objective,
        strategy=metric_strategy,
        threshold=threshold,
      )
      metric_list.append(new_metric)
    return metric_list

  @classmethod
  def get_constraints_from_json(cls, json_dict, parameters):
    # pylint: disable=too-many-locals,too-many-statements
    constraints = get_opt_with_validation(
      json_dict,
      "linear_constraints",
      ValidationType.arrayOf(ValidationType.object),
    )
    if not constraints:
      return []

    parameter_names = []
    double_params_names = []
    integer_params_names = []
    unconditioned_params_names = []
    log_transform_params_names = []
    grid_param_names = []
    for p in parameters:
      parameter_names.append(p.name)
      if p.grid_values:
        grid_param_names.append(p.name)
      if p.param_type == PARAMETER_DOUBLE:
        double_params_names.append(p.name)
      if p.param_type == PARAMETER_INT:
        integer_params_names.append(p.name)
      if p.param_type in [PARAMETER_DOUBLE, PARAMETER_INT]:
        if not p.conditions:
          unconditioned_params_names.append(p.name)
        if p.transformation == ExperimentParameter.TRANSFORMATION_LOG:
          log_transform_params_names.append(p.name)

    constraint_lst = []
    constrained_integer_variables = set()

    for c in constraints:
      constraint_type = get_opt_with_validation(c, "type", ValidationType.string)
      terms = get_opt_with_validation(c, "terms", ValidationType.arrayOf(ValidationType.object))
      rhs = get_opt_with_validation(c, "threshold", ValidationType.number)

      term_lst = []
      constraint_var_set = set()
      if len(terms) < 1:
        raise InvalidValueError("Constraint must have at least one term")

      term_types = ["double" if term["name"] in double_params_names else "int" for term in terms]
      if len(set(term_types)) > 1:
        raise InvalidValueError("Constraint functions cannot mix integers and doubles. One or the other only.")
      for term in terms:
        coeff = get_opt_with_validation(term, "weight", ValidationType.number)
        if coeff == 0:
          continue
        name = get_opt_with_validation(term, "name", ValidationType.string)
        name = validate_variable_name(name)
        if name in integer_params_names:
          constrained_integer_variables.add(name)
        if len(constrained_integer_variables) > MAX_NUM_INT_CONSTRAINT_VARIABLES:
          raise InvalidValueError(
            f"SigOpt allows no more than {MAX_NUM_INT_CONSTRAINT_VARIABLES} integer constraint variables"
          )
        if name not in parameter_names:
          raise InvalidValueError(f"Variable {name} is not a known parameter")
        if name not in double_params_names and name not in integer_params_names:
          raise InvalidValueError(f"Variable {name} is not a parameter of type `double` or type `int`")
        if name not in unconditioned_params_names:
          raise InvalidValueError(f"Constraint cannot be defined on a conditioned parameter {name}")
        if name in log_transform_params_names:
          raise InvalidValueError(f"Constraint cannot be defined on a log-transformed parameter {name}")
        if name in grid_param_names:
          raise InvalidValueError(f"Constraint cannot be defined on a grid parameter {name}")
        if name in constraint_var_set:
          raise InvalidValueError(f"Duplicate variable name: {name}")
        constraint_var_set.add(name)

        term_lst.append(Term(coeff=coeff, name=name))
      constraint_lst.append(ExperimentConstraint(type=constraint_type, terms=term_lst, rhs=rhs))
    return constraint_lst

  @classmethod
  def get_num_solutions_from_json(cls, json_dict, parameters):
    num_solutions = get_opt_with_validation(json_dict, "num_solutions", ValidationType.positive_integer)
    return num_solutions

  @classmethod
  def get_parallel_bandwidth_from_json(cls, json_dict):
    return get_opt_with_validation(json_dict, "parallel_bandwidth", ValidationType.positive_integer)

  @classmethod
  def get_tasks_from_json(cls, json_dict):
    task_list_input = get_opt_with_validation(json_dict, "tasks", ValidationType.arrayOf(ValidationType.object))
    if not task_list_input:
      return []

    tasks = []
    for task in task_list_input:
      name = get_opt_with_validation(task, "name", ValidationType.string)
      cost = get_opt_with_validation(task, "cost", ValidationType.number)
      tasks.append(Task(name=name, cost=cost))
      if cost <= 0 or cost > 1:
        raise BadParamError("For multitask experiments, costs must all be positive and less than or equal to 1.")

    distinct_costs = distinct([t.cost for t in tasks])
    distinct_names = distinct([t.name for t in tasks])
    if 1 not in distinct_costs:
      raise BadParamError("For multitask experiments, exactly one task must have cost == 1 (none present).")
    if len(distinct_costs) != len(tasks):
      raise BadParamError("For multitask experiments, all task costs must be distinct.")
    if len(distinct_names) != len(tasks):
      raise BadParamError("For multitask experiments, all task names must be distinct.")
    if len(tasks) < 2:
      raise BadParamError("For multitask experiments, at least 2 tasks must be present.")

    return tasks


class ExperimentsCreateHandler(BaseExperimentsCreateHandler):
  """Create an experiment
    This creates an experiment with specified parameters for the user with the client associated with this token.
    ---
      tags:
        - "experiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExperimentPost"
      responses:
        201:
          description: "New Experiment created."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Experiment'
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 201."
        401:
          description: "Unauthorized. Authorization was incorrect."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        tags:
          - name: experiments
            description: "Operations on the Experiment object as a first class object"
        schemas:
          Conditionals:
            type: object
            description: "Provides the ability to turn on and off a parameter subject to various other criteria. This is
                          the setup for a conditional. Must be created at beginning of experiment."
            properties:
              name:
                type: string
                description: "Name of the conditional, so that it can be referenced by the specific parameter that wants
                              to turn it off."
              values:
                type: array
                items:
                  type: string
                minItems: 2
                description: "The potential values of the conditional. This feature is at present only available for
                                categorial parameters, which is why this must be strings."
          ExperimentPost:
            type: object
            allOf:
              - $ref: '#/components/schemas/ExperimentBase'

          ExperimentBase:
            type: object
            required: [name, parameters, metrics]
            properties:
              linear_constraints:
                type: array
                items:
                  $ref: '#/components/schemas/Linear_Constraint'
                description: "When experiment type is offline, this gives you the ability to express linear
                              inequalities that relate multiple parameters. Only valid for offline."
              metadata:
                type: object
                description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                              strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                              client side."
              metrics:
                type: array
                items:
                  $ref: '#/components/schemas/Metric'
              name:
                type: string
                description: "Human readable name for experiment."
                minLength: 1
                maxLength: 100
              num_solutions:
                type: integer
                minimum: 1
                description: "The number of (diverse) solutions that SigOpt will search for. Multiple solutions are
                              only supported when no parameters of type categorical are present."
              budget:
                type: integer
                minimum: 1
                description: "The expected number of runs in an experiment. Not doing as many runs as specified in the
                              budget will lead to SigOpt insufficiently exploring the n-dimensional parameter space.
                              Required when more than 1 optimized metric exists or for any constrained metrics.
                              Required for grid searches, multisolution or tasks enabled searches.
                              This makes our Sigopt optimizers much more effective and is recommended for all cases."
              conditionals:
                type: array
                description: "List of conditional on parameters associated with experiment. Can only be set at
                              beginning of experiment and not updated."
                items:
                  $ref: '#/components/schemas/Conditionals'
              parallel_bandwidth:
                type: integer
                minimum: 1
                description: "The number of simultaneous runs you plan to simultaneously be training and evaluating
                              during this experiment."
              project:
                type: string
                description: "Reference ID of an existing project to associate this experiment with."
              type:
                type: string
                description: "Type of experiment. Grid is a comprehensive, linear search of the n-dimensional space
                              defined by the set of parameters. Random is a random search of those parameters, without
                                optimization. Offline uses the SigOpt intelligent optimization techniques."
                enum: ["grid", "offline", "random"]
                default: "offline"
              parameters:
                type: array
                description: "The parameters of this experiment, the independent variables that SigOpt will be
                              providing suggestions for."
                minItems: 1
                items:
                  $ref: '#/components/schemas/Parameter'
              tasks:
                type: array
                items:
                  $ref: '#/components/schemas/Task'
                description: "A task is a very fast approximation of a metric, but not its actual value. Commonly
                              used in gradient descent algorithms, this allows the SigOpt optimziation engine to
                              quickly get better results, by controlling the level of approximation. One of the tasks
                              must have a cost of 1, that is the full correct calulation of the metric. This requires
                              an observation budget, and is not supported with multisolution, multiple optimized
                              metrics, or any number of constraint metrics. Must be created at
                              beginning of experiment and cannot be updated later."
                minItems: 2
              runs_only:
                type: boolean
                description: "If true, experiment will use only the new training_run interface,
                    automatically creating suggestions and observations every time a run is created. Otherwise the
                    client has to manage that themselves."
                default: false

          Experiment:
            allOf:
              - $ref: '#/components/schemas/ExperimentBase'
              - type: object
                properties:
                  client:
                    type: integer
                    description: "Id of the client that is associated with creating this experiment."
                  created:
                    type: integer
                    description: "Epoch time for when the experiment was created."
                  conditionals:
                    type: array
                    items:
                      $ref: '#/components/schemas/Conditionals'
                  development:
                    type: boolean
                    description: "Is a development experiment, results will be always be random, not optimized; intended
                                  for integration testing."
                  id:
                    type: integer
                    description: "Experiment Id."
                  state:
                    type: string
                    enum: [deleted, active]
                  updated:
                    type: integer
                    description: "Epoch time of last update to experiment (including new training run associated with
                                  experiment)."
                  user:
                    type: integer
                    description: "ID of user who created experiment."
                  progress:
                    oneOf:
                      - $ref: '#/components/schemas/RunProgress'
                      - $ref: '#/components/schemas/ObservationProgress'
          Linear_Constraint:
            type: object
            description: "This object gives you the ability to represent mathematical relationships between multiple
                          parameters. SigOpt will only suggest runs where this holds. The equations must be in the form
                          (w1*param1) + (w2*param2) ... greater than or less than the threshold."
            properties:
              type:
                type: string
                enum: ["less_than", "greater_than"]
              threshold:
                type: number
                description: "The constant on one end of the equation."
              terms:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                      description: "Must be the name of a parameter of type double."
                    weight:
                      type: number
                      description: "The coeffcient for the specific parameter in the inequality equation."
          Metric:
            type: object
            description: "Variable that will be tracked with a run. Each one represents a dependent variable in the
                          experiment that your code must report back to prepare for the next optimization run."
            required: [name]
            properties:
              name:
                type: string
              objective:
                type: string
                enum: ["maximize", "minimize"]
                default: "maximize"
              strategy:
                type: string
                enum: ["optimize", "store", "constraint"]
                default: "optimize"
              threshold:
                type: number
                description: "What is the minimum (or maxiumum if objective is minimize) desired value for a given
                metric. What do you want this metric to be closest too? Required when metric strategy is constraint."
          ObservationProgress:
            type: object
            properties:
              observation_count:
                type: integer
                minimum: 0
              observation_budget_consumed:
                type: number
                minimum: 0
              first_observation:
                type: object
              last_observation:
                type: object
              best_observation:
                type: object
          Parameter:
            type: object
            required: [name, type]
            properties:
              name:
                type: string
                description: "Name of the parameter. No duplicates allowed in the array."
              type:
                type: string
                enum: ["categorical", "double", "int"]
                description: "Type of the parameter. Categorical means a set of strings, double and int are number and
                              integer, respectively."
              transformation:
                type: string
                enum: ["none", "log"]
                description: "Only an option if parameter type is double, otherwise cannot be present. If set to 'log'
                              then this will be treated as a paremeter in log-space."
              grid:
                type: array
                items:
                  oneOf:
                    - type: integer
                    - type: number
                description: "If experiment type is grid, this can be a list of values to try for this parameter. No
                              duplicates allowed."
              bounds:
                type: object
                description: "If experiment type is grid and grid is not defined for this parameter and the parameter is
                              double or int, this must be set."
                properties:
                  min:
                    oneOf:
                      - type: integer
                      - type: number
                    description: "The minimum value that the SigOpt optimizer will search. Must be same type as
                                  parameter type."
                  max:
                    oneOf:
                      - type: integer
                      - type: number
                    description: "The maxium value that the Sigopt optimizer will search. Must be same type as parameter
                                  type."
              prior:
                type: object
                description: "Only applies to parameters type of double. This allows you to define a prior belief on the
                              distribution of this parameter."
                properties:
                  name:
                    type: string
                    enum: ["normal", "beta"]
                  mean:
                    type: number
                    description: "Only applies for prior type 'normal.' This must be within any bounds provided."
                  scale:
                    type: number
                    description: "Only applies for prior type 'normal.' This number must be positive."
                  shape_a:
                    type: number
                    description: "Only applies for prior type 'beta.' This number must be positive."
                  shape_b:
                    type: number
                    description: "Only applies for prior type 'beta.' This number must be positive."
              categorical_values:
                type: array
                description: "This is the set of potential categorical values. If type is 'categorical' this is
                              required, otherwise not present. A single experiment can only have a total of 10
                              categorical values across all categorical parameters."
                items:
                    type: string
              default_value:
                description: "The default value for this parameter if not assigned. If parameter type is double and
                              transformation is log, must be positive. This is required for all parameters added after
                              experiment creation. Type must match parameter type."
                oneOf:
                  - type: integer
                  - type: number
                  - type: string
          RunProgress:
            type: object
            properties:
              finished_run_count:
                type: integer
                minimum: 0
              active_run_count:
                type: integer
                minimum: 0
              total_run_count:
                type: integer
                minimum: 0
              remaining_budget:
                nullable: true
                type: integer
          Task:
            type: object
            properties:
              name:
                type: string
                description: "This name is associated with the specified level. Must be unique."
              cost:
                type: number
                minimum: 0
                maximum: 1
                description: "The cost associated with this approximation method, as a fraction of the full, correct
                              value (which is always 1, but must be included). Costs must be distinct."

    """

  authenticator = client_token_authentication
  required_permissions = WRITE

  def get_client(self):
    return self.auth.current_client

  def can_act_on_objects(self, requested_permission, objects):
    return (
      super().can_act_on_objects(requested_permission, objects)
      and self.auth.current_client
      and self.auth.can_act_on_client(self.services, requested_permission, self.auth.current_client)
    )


class ClientsExperimentsCreateHandler(ClientHandler, BaseExperimentsCreateHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def get_client(self):
    return self.client
