# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.constant import (
  EXPERIMENT_PARAMETER_TYPE_TO_NAME,
  METRIC_OBJECTIVE_NAME_TO_TYPE,
  METRIC_STRATEGY_NAME_TO_TYPE,
  PARAMETER_TRANSFORMATION_TYPE_TO_NAME,
)
from zigopt.experiment.model import Experiment, ExperimentMetaProxy, ExperimentParameterProxy
from zigopt.handlers.experiments.base import ExperimentHandler, get_budget_param
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.handlers.validate.experiment import (
  validate_experiment_json_dict_for_update,
  validate_experiment_name,
  validate_state,
)
from zigopt.handlers.validate.validate_dict import (
  ValidationType,
  get_opt_with_validation,
  get_with_validation,
  key_present,
)
from zigopt.net.errors import BadParamError, NotFoundError
from zigopt.parameters.from_json import (
  set_bounds_from_json,
  set_categorical_value_from_json,
  set_default_value_from_json,
  set_experiment_parameter_from_json,
  set_grid_values_from_json,
  set_parameter_type_from_json,
  set_prior_from_json,
  set_transformation_from_json,
)
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta, ExperimentMetric
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from libsigopt.aux.errors import InvalidValueError, MissingJsonKeyError


class ExperimentsUpdateHandler(ExperimentHandler):
  """Update an already existing experiment.
    This takes an already existing experiment and sets its new values. Only the values
    that need to be changed should be included in this object, not any existing and unchanged fields. Thus,
    any field not mentioned explicitly in this PUT schema can't be changed after the Experiment object is created.
    This is conceptually more like a RESTful PATCH call, however for historical reasons we use the PUT verb instead.

    This is complicated by arrays of objects parameters and metrics. For those arrays you do need to
    include all of the previous and new objects, because we will remove any object that is not present in the array.
    For those objects all of the same rules as creation continue to apply.
    ---
      tags:
          - "experiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExperimentPut"
      responses:
        200:
          description: "Experiment updated."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Experiment'
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 200, without any data."
        401:
          description: "Unauthorized. Authorization was incorrect."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        404:
          description: "Not found. No experiment is at that URI."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        schemas:
          ExperimentPut:
            type: object
            required: [name, parameters, metrics, id]
            properties:
              name:
                type: string
                description: "Human readable name for experiment."
                minLength: 1
                maxLength: 100
              project:
                type: string
                description: "Reference ID of an existing project to associate this experiment with. If explicitly
                              set to none, will not be part of any project, otherwise this will set to the
                              specified project. Can only be associated with one project at a time."
              no_optimize:
                type: boolean
                description: "If true, then the next suggestion will not be affected by this update. Useful for bulk
                              updates that are not affecting any parameters, metrics, etc. We will always honor this
                              field if present, we might or might not recalculate suggestions after experiment updates
                              if not present."
              state:
                type: string
                enum: [deleted, active]
              parameters:
                type: array
                description: "The parameters of this experiment, the independent variables that SigOpt will be
                              providing suggestions for. Any additional parameters require default values.
                              To delete a parameter, remove it from the array. If a new one is added, it must
                              have a default_value set which will be used for all currently existing runs. Type
                              of parameter CANNOT be changed. Bounds and grid will be set directly to the new values.
                              To remove a category from a categorical parameter, just don't include it in the array.
                              There must still be at least two non-deleted categories, however. Priors can be updated
                              like normal. If a transformation was set on a parameter, it cannot be changed."
                minItems: 1
                items:
                  $ref: '#/components/schemas/Parameter'
              metrics:
                type: array
                items:
                  $ref: '#/components/schemas/Metric'
                description: "Metric names cannot be changed. The number of metrics cannot be changed. Metric
                              objectives cannot be changed. Metric strategy cannot be changed. The only thing
                              that can be changed is the metric threshold- if that is set to null we will remove,
                              otherwise set to the provided value."
              parallel_bandwidth:
                type: integer
                minimum: 1
                default: 1
                description: "The number of simultaneous runs you plan to simultaneously be training and evaluating
                              during this experiment. If this is included but set to NULL we will default to 1."
              budget:
                type: integer
                minimum: 1
                description: "The expected number of runs in an experiment. Not doing as many runs as specified in the
                              budget will lead to SigOpt insufficiently exploring the n-dimensional parameter space.
                              Required when more than 1 optimized metric exists or for any constrained metrics.
                              Required for grid searches, multisolution or tasks enabled searches.
                              This makes our Sigopt optimizers much more effective and is recommended for all cases.
                              Cannot be updated in cases of grid searches, multi-optimized metrics, or multi-solution."
              metadata:
                type: object
                description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                              strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                              client side."
    """

  authenticator = api_token_authentication
  required_permissions = WRITE

  @classmethod
  def validate_json_params(cls, data):
    validate_experiment_json_dict_for_update(data)

  @classmethod
  def get_budget_key_and_value(cls, json_dict, runs_only):
    budget, budget_key = get_budget_param(json_dict, runs_only, return_key=True)
    return budget_key, budget

  def parse_params(self, request):
    json_data = request.params()
    self.validate_json_params(json_data)
    return json_data

  get_project = BaseExperimentsCreateHandler.get_project

  def get_client(self):
    return self.client

  def _check_unsupported_updates(self, json_dict):
    if "constraints" in json_dict:
      raise BadParamError("Constraints cannot be updated for an experiment")

    if "num_solutions" in json_dict:
      raise BadParamError("Number of solutions cannot be updated for an experiment")

    if "conditionals" in json_dict:
      raise BadParamError("Conditionals cannot be updated for an experiment")

    if "tasks" in json_dict:
      raise BadParamError("The tasks of a multitask experiment cannot be updated after creation")

  def _get_project(self, json_dict, update_experiment_fields):
    if "project" not in json_dict:
      return self.services.project_service.find_by_client_and_id(
        client_id=self.experiment.client_id,
        project_id=self.experiment.project_id,
      )
    project = self.get_project(json_dict)
    if self.experiment.runs_only:
      if project is None:
        raise BadParamError("This experiment cannot be removed from the project.")
      if project.id != self.experiment.project_id:
        raise BadParamError("This experiment's project cannot be changed.")
    update_experiment_fields[Experiment.project_id] = project and project.id
    return project

  def _maybe_set_name(self, json_dict, update_experiment_fields):
    if "name" not in json_dict:
      return
    name = get_with_validation(json_dict, "name", ValidationType.string)
    validate_experiment_name(name)
    update_experiment_fields[Experiment.name] = name
    self.experiment.name = name

  def _maybe_set_state(self, json_dict, update_experiment_fields):
    if "state" not in json_dict:
      return
    state = get_with_validation(json_dict, "state", ValidationType.string)
    state = validate_state(state)
    deleted = state == "deleted"
    update_experiment_fields[Experiment.deleted] = deleted
    self.experiment.deleted = deleted

  def _maybe_set_budget(self, json_dict, new_meta, update_meta_fields):
    try:
      budget_key, budget = self.get_budget_key_and_value(json_dict, self.experiment.runs_only)
    except MissingJsonKeyError:
      return
    if self.experiment.experiment_type == ExperimentMeta.GRID:
      raise BadParamError(f"`{budget_key}` cannot be updated for experiments of type `grid`.")
    if self.experiment.requires_pareto_frontier_optimization:
      raise BadParamError(f"`{budget_key}` cannot be updated for experiments with more than one optimized metric.")
    if self.experiment.num_solutions > 1:
      raise BadParamError(f"`{budget_key}` cannot be updated for experiments with more than one solution.")
    update_meta_fields[Experiment.experiment_meta.observation_budget] = budget
    if budget is not None:
      new_meta.observation_budget = budget
    else:
      new_meta.ClearField("observation_budget")

  def _maybe_set_parameters(self, json_dict, new_meta, update_meta_fields):
    if "parameters" not in json_dict:
      return
    if self.experiment.experiment_type == ExperimentMeta.GRID:
      raise BadParamError("Parameters cannot be updated for experiments of type `grid`.")
    if self.experiment.constraints:
      raise BadParamError("Parameters cannot be updated for experiments with constraints")

    parameters_json = get_with_validation(
      json_dict,
      "parameters",
      ValidationType.arrayOf(ValidationType.object),
    )

    if not parameters_json:
      raise BadParamError("Experiments must have at least one parameter.")

    name_counts = distinct_counts(remove_nones([p.get("name") for p in parameters_json]))
    duplicates = [key for (key, value) in name_counts.items() if value > 1]
    if len(duplicates) > 0:
      raise BadParamError(f"Duplicate parameter names: {duplicates}")

    self.update_parameters(new_meta, parameters_json, self.experiment.experiment_type)
    update_meta_fields[Experiment.experiment_meta.all_parameters_unsorted] = list(new_meta.all_parameters_unsorted)

  def _maybe_set_metadata(self, json_dict, new_meta, update_meta_fields):
    if "metadata" not in json_dict:
      return
    client_provided_data = BaseExperimentsCreateHandler.get_client_provided_data(json_dict)
    update_meta_fields[Experiment.experiment_meta.client_provided_data] = client_provided_data
    if client_provided_data is not None:
      new_meta.client_provided_data = client_provided_data
    else:
      new_meta.ClearField("client_provided_data")

  def _maybe_set_parallel_bandwidth(self, json_dict, new_meta, update_meta_fields):
    if "parallel_bandwidth" not in json_dict:
      return
    parallel_bandwidth = BaseExperimentsCreateHandler.get_parallel_bandwidth_from_json(json_dict)
    if parallel_bandwidth is None:
      new_meta.ClearField("parallel_bandwidth")
    else:
      new_meta.parallel_bandwidth = parallel_bandwidth
    update_meta_fields[Experiment.experiment_meta.parallel_bandwidth] = parallel_bandwidth

  def _maybe_set_metrics(self, json_dict, new_meta, update_meta_fields):
    if "metrics" not in json_dict:
      return
    self.update_metrics(
      update_meta_fields,
      json_dict,
      new_meta,
    )

  def handle(self, json_dict):
    no_optimize = get_opt_with_validation(json_dict, "no_optimize", ValidationType.boolean)

    validate_experiment_json_dict_for_update(json_dict)
    self._check_unsupported_updates(json_dict)

    client = self.services.client_service.find_by_id(self.experiment.client_id, current_client=self.auth.current_client)

    update_meta_fields = {}
    update_experiment_fields = {}
    new_meta = self.experiment.experiment_meta.copy_protobuf()
    if not new_meta.metrics:
      new_meta.metrics.extend([ExperimentMetric(name=None)])

    project = self._get_project(json_dict, update_experiment_fields)

    self._maybe_set_name(json_dict, update_experiment_fields)

    self._maybe_set_state(json_dict, update_experiment_fields)

    self._maybe_set_budget(json_dict, new_meta, update_meta_fields)

    self._maybe_set_parameters(json_dict, new_meta, update_meta_fields)

    self._maybe_set_metadata(json_dict, new_meta, update_meta_fields)

    self._maybe_set_parallel_bandwidth(json_dict, new_meta, update_meta_fields)

    self._maybe_set_metrics(json_dict, new_meta, update_meta_fields)

    self.experiment.experiment_meta = new_meta

    self.services.experiment_service.verify_experiment_acceptability(
      self.auth,
      self.experiment,
      client,
    )

    # TODO(SN-1089): Make these into one query
    if update_meta_fields:
      update_count = self.services.experiment_service.update_meta(self.experiment.id, update_meta_fields)
      if update_count == 0:
        raise NotFoundError(f"No experiment {self.experiment.id}")

    original_project_id = self.experiment.project_id

    update_experiment_fields["date_updated"] = current_datetime()
    self.experiment.date_updated = update_experiment_fields["date_updated"]
    update_count = self.services.database_service.update_one(
      self.services.database_service.query(Experiment).filter(Experiment.id == self.experiment.id),
      update_experiment_fields,
    )
    if update_count == 0:
      raise NotFoundError(f"No experiment {self.experiment.id}")

    if original_project_id is not None:
      self.services.project_service.mark_as_updated_by_experiment(
        experiment=self.experiment,
        project_id=original_project_id,
      )
    if project is not None and project.id != original_project_id:
      self.services.project_service.mark_as_updated_by_experiment(
        experiment=self.experiment,
        project_id=project.id,
      )

    if no_optimize is not True:
      self._reset_hyperparameters()

    progress = self.services.experiment_progress_service.progress_for_experiments([self.experiment])[self.experiment.id]
    return self.JsonBuilder(self.experiment, project=project, progress_builder=progress.json_builder())

  @generator_to_safe_iterator
  def _compare_metric_jsons_with_metrics_by_name(self, json_dict, metrics):
    if len(metrics) == 1:
      return ((metric_json, metric) for metric_json, metric in zip(json_dict["metrics"], metrics))
    metric_json_map = {metric_json["name"]: metric_json for metric_json in json_dict["metrics"]}
    return ((metric_json_map[metric.name], metric) for metric in metrics)

  def _update_thresholds_on_metrics(self, json_dict, new_meta):
    for metric_json, metric in self._compare_metric_jsons_with_metrics_by_name(json_dict, new_meta.metrics):
      if key_present(metric_json, "threshold"):
        new_threshold = get_opt_with_validation(metric_json, "threshold", ValidationType.number)
        if new_threshold is None:
          metric.ClearField("threshold")
        else:
          metric.threshold = new_threshold

  def _raise_if_objective_changed(self, json_dict, metrics):
    for metric_json, metric in self._compare_metric_jsons_with_metrics_by_name(json_dict, metrics):
      if key_present(metric_json, "objective"):
        if METRIC_OBJECTIVE_NAME_TO_TYPE.get(metric_json["objective"]) != metric.objective:
          raise BadParamError("Changing the objective of a metric is forbidden")

  def _raise_if_strategy_changed(self, json_dict, metrics):
    for metric_json, metric in self._compare_metric_jsons_with_metrics_by_name(json_dict, metrics):
      if key_present(metric_json, "strategy"):
        if METRIC_STRATEGY_NAME_TO_TYPE.get(metric_json["strategy"]) != metric.strategy:
          raise BadParamError("Changing the strategy of a metric is forbidden")

  def _raise_if_invalid_name(self, json_dict, metrics):
    experiment_metric_names = [metric.name for metric in metrics]
    if len(metrics) > 1:
      if any(not key_present(metric_json, "name") for metric_json in json_dict["metrics"]):
        raise BadParamError(
          "The `name` field must be specified for every metric in experiments with more than one metric"
        )
      provided_metric_names = [metric_json["name"] for metric_json in json_dict["metrics"]]
    else:
      metric_json = json_dict["metrics"][0]
      # in the single metric case, check the case where no name is provided in the update call
      provided_metric_names = [metric_json["name"]] if key_present(metric_json, "name") else [metrics[0].name]
      # if null name is provided we must convert to empty string since that is the protobuf unnamed metric name
      provided_metric_names = [coalesce(name, "") for name in provided_metric_names]
    if set(provided_metric_names) != set(experiment_metric_names):
      raise BadParamError("Changing the name of a metric is forbidden")

  def _raise_if_threshold_specified(self, json_dict, metrics):
    num_optimized_metrics = len([metric for metric in metrics if metric.is_optimized])

    for metric_json, metric in self._compare_metric_jsons_with_metrics_by_name(json_dict, metrics):
      # Reuse get_metric_threshold to throw the appropriate BadParamErrors
      BaseExperimentsCreateHandler.get_metric_threshold(metric_json, num_optimized_metrics, metric.strategy)

  def _raise_if_num_metrics_changed(self, json_dict, metrics):
    if len(json_dict["metrics"]) != len(metrics):
      raise BadParamError("Changing the number of metrics is forbidden")

  def _raise_if_bad_update(self, json_dict, metrics):
    if not is_sequence(json_dict.get("metrics", None)):
      raise BadParamError("Metrics must be an array.")
    self._raise_if_num_metrics_changed(json_dict, metrics)
    self._raise_if_invalid_name(json_dict, metrics)
    self._raise_if_objective_changed(json_dict, metrics)
    self._raise_if_strategy_changed(json_dict, metrics)
    self._raise_if_threshold_specified(json_dict, metrics)

  def update_metrics(self, update_meta_fields, json_dict, new_meta):
    metrics = self.experiment.all_metrics
    self._raise_if_bad_update(json_dict, metrics)
    self._update_thresholds_on_metrics(json_dict, new_meta)
    update_meta_fields[Experiment.experiment_meta.metrics] = new_meta.metrics

  def update_parameters(self, meta, parameters_json, experiment_type):
    parameter_map = dict(((p.name, p) for p in meta.all_parameters_unsorted))
    seen_names = set()
    for parameter_json in parameters_json:
      name = get_with_validation(parameter_json, "name", ValidationType.string)
      is_new = False
      try:
        parameter = parameter_map[name]
      except KeyError:
        parameter = meta.all_parameters_unsorted.add()
        set_experiment_parameter_from_json(
          parameter,
          parameter_json,
          meta.experiment_type,
          ExperimentMetaProxy(meta).conditionals_map,
        )
        is_new = True
      else:
        is_new = parameter.deleted
        self.update_param(parameter, parameter_json, experiment_type)
      parameter = ExperimentParameterProxy(parameter)
      self.validate_default_value(parameter, is_new=is_new)

      if name in seen_names:
        raise InvalidValueError(f"Duplicate parameter name: {parameter.name}")
      seen_names.add(name)

    for parameter in meta.all_parameters_unsorted:
      if parameter.name not in seen_names:
        parameter.deleted = True

  def validate_default_value(self, param, is_new):
    if is_new:
      if not param.HasField("replacement_value_if_missing"):
        raise BadParamError(
          "New parameters must have default values."
          " Please add a default_value field to the new parameter(s)."
          " Or if you are using the web dashboard fill out the Default Value field."
        )
    default_value = param.GetFieldOrNone("replacement_value_if_missing")
    if default_value is not None and not param.valid_assignment(default_value):
      if param.is_categorical:
        raise BadParamError(
          f"`default_value` for parameter {param.name} is invalid - must be a valid categorical value."
        )
      if param.is_grid:
        raise BadParamError(f"`default_value` for parameter {param.name} is invalid - must be a valid grid value.")
      raise BadParamError(
        f"`default_value` for parameter {param.name} is invalid"
        f" - must be between {param.bounds.minimum} and {param.bounds.maximum}"
      )

  def _maybe_set_parameter_type(self, parameter, parameter_json):
    if "type" not in parameter_json:
      return
    param_type = parameter.param_type
    set_parameter_type_from_json(parameter, parameter_json)
    if parameter.param_type != param_type:
      raise BadParamError(
        f"`type` attribute on parameter {parameter.name}"
        f" must remain {EXPERIMENT_PARAMETER_TYPE_TO_NAME.get(param_type)}"
      )

  def _maybe_set_parameter_bounds(self, parameter, parameter_json, experiment_type):
    if "bounds" not in parameter_json and "grid" not in parameter_json:
      return
    set_bounds_from_json(parameter, parameter_json, experiment_type)

  def _maybe_set_parameter_grid_values(self, parameter, parameter_json):
    if "grid" not in parameter_json:
      return
    set_grid_values_from_json(parameter, parameter_json)

  def _maybe_set_parameter_categorical_values(self, parameter, parameter_json):
    categorical_values_json = get_opt_with_validation(
      parameter_json,
      "categorical_values",
      ValidationType.arrayOf(ValidationType.oneOf([ValidationType.object, ValidationType.string])),
    )
    if categorical_values_json is None:
      return

    categorical_values_map = dict((c.name, c) for c in parameter.all_categorical_values)
    try:
      enum_index = max((c.enum_index for c in parameter.all_categorical_values)) + 1
    except ValueError:
      enum_index = 1

    seen_names = set()
    for categorical_value_json in categorical_values_json:
      if is_string(categorical_value_json):
        name = categorical_value_json
      else:
        name = get_with_validation(categorical_value_json, "name", ValidationType.string)
      try:
        categorical_value = categorical_values_map[name]
        categorical_value.ClearField("deleted")
      except KeyError:
        categorical_value = parameter.all_categorical_values.add()
        set_categorical_value_from_json(categorical_value, categorical_value_json, enum_index)
        enum_index += 1

      if categorical_value.name in seen_names:
        raise BadParamError(f"Duplicate categorical value {categorical_value.name} for parameter {parameter.name}")
      seen_names.add(categorical_value.name)

    for categorical_value in parameter.all_categorical_values:
      if categorical_value.name not in seen_names:
        categorical_value.deleted = True

    if len([c for c in parameter.all_categorical_values if not c.deleted]) < 2:
      raise BadParamError(f"Parameters {parameter.name} must have 2 or more active (not deleted) categorical values")

  def _maybe_set_parameter_default_value(self, parameter, parameter_json):
    if "default_value" not in parameter_json:
      return
    set_default_value_from_json(parameter, parameter_json)

  def _maybe_set_parameter_prior(self, parameter, parameter_json):
    if "prior" not in parameter_json:
      return
    if parameter_json["prior"] is None:
      parameter.ClearField("prior")
    else:
      set_prior_from_json(parameter, parameter_json)

  def _maybe_set_parameter_transformation(self, parameter, parameter_json):
    if "transformation" not in parameter_json:
      return
    original_transformation = parameter.transformation
    set_transformation_from_json(parameter, parameter_json)
    if parameter.transformation != original_transformation:
      raise BadParamError(
        f"`transformation` attribute on parameter {parameter.name}"
        f" must remain {PARAMETER_TRANSFORMATION_TYPE_TO_NAME.get(original_transformation)}"
      )

  def update_param(self, parameter, parameter_json, experiment_type):
    if "conditions" in parameter_json:
      raise BadParamError("Conditions cannot be updated for parameters")

    self._maybe_set_parameter_type(parameter, parameter_json)

    self._maybe_set_parameter_bounds(parameter, parameter_json, experiment_type)

    self._maybe_set_parameter_grid_values(parameter, parameter_json)

    self._maybe_set_parameter_categorical_values(parameter, parameter_json)

    self._maybe_set_parameter_default_value(parameter, parameter_json)

    self._maybe_set_parameter_prior(parameter, parameter_json)

    self._maybe_set_parameter_transformation(parameter, parameter_json)

    parameter.ClearField("deleted")
