# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, ForeignKeyConstraint, Index, String
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.experiment.constraints import parse_constraints_to_halfspaces
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  MAXIMIZE,
  MINIMIZE,
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentMetric,
  ExperimentParameter,
)
from zigopt.protobuf.proxy import Proxy


class ExperimentParameterProxy(Proxy):
  def __init__(self, underlying):
    super().__init__(underlying)
    self.active_categorical_values_map_by_index = dict(((c.enum_index, c) for c in self.active_categorical_values))
    self.all_categorical_values_map = dict(((c.name, c) for c in self.all_categorical_values))
    self.all_categorical_values_map_by_index = dict(((c.enum_index, c) for c in self.all_categorical_values))

  @property
  def is_categorical(self):
    return self.param_type == PARAMETER_CATEGORICAL

  @property
  def is_double(self):
    return self.param_type == PARAMETER_DOUBLE

  @property
  def is_integer(self):
    return self.param_type == PARAMETER_INT

  @property
  def is_grid(self):
    return len(self.grid_values) > 0

  @property
  def has_prior(self):
    return self.GetFieldOrNone("prior") is not None

  @property
  def active_categorical_values(self):
    return tuple((c for c in self.all_categorical_values if not c.deleted))

  def valid_assignment(self, assignment):
    if self.is_categorical:
      if assignment not in self.active_categorical_values_map_by_index:
        return False
    elif self.is_grid:
      if assignment not in self.grid_values:
        return False
    else:
      if not self.bounds.minimum <= assignment <= self.bounds.maximum:
        return False
    return True

  @property
  def has_log_transformation(self):
    return self.transformation == ExperimentParameter.TRANSFORMATION_LOG


class ExperimentMetricProxy(Proxy):
  @property
  def is_minimized(self):
    return self.objective == MINIMIZE

  @property
  def is_maximized(self):
    return self.objective == MAXIMIZE

  @property
  def threshold(self):
    return self.GetFieldOrNone("threshold")

  @property
  def is_optimized(self):
    return self.strategy == ExperimentMetric.OPTIMIZE

  @property
  def is_constraint(self):
    return self.strategy == ExperimentMetric.CONSTRAINT


class ExperimentMetaProxy(Proxy):
  def __init__(self, underlying):
    super().__init__(underlying)
    self._parameters = tuple((ExperimentParameterProxy(p) for p in underlying.all_parameters_unsorted)) or ()
    self.all_parameters_sorted = sorted([p for p in self._parameters if not p.deleted], key=lambda x: x.name)
    self.double_parameters_sorted = tuple(
      p for p in self.all_parameters_sorted if p.is_double and not p.deleted and not p.grid_values
    )
    self.all_parameters_map = dict(((p.name, p) for p in self.all_parameters))
    self.all_parameters_including_deleted_map = dict(((p.name, p) for p in self.all_parameters_including_deleted))
    self.conditionals_map = dict((c.name, c) for c in self.conditionals)

    for m in underlying.metrics:
      if m.name == "":
        m.ClearField("name")

    self.has_user_defined_metric = bool(underlying.metrics)
    self._metrics = tuple((ExperimentMetricProxy(m) for m in underlying.metrics)) or tuple(
      (ExperimentMetricProxy(ExperimentMetric()),)
    )
    self.all_metrics_sorted = sorted(self._metrics, key=lambda m: m.name)

    constrained_variables = []
    if self.has_constraints:
      for constraint in self.constraints:
        constrained_variables = constrained_variables + [term.name for term in constraint.terms]
      constrained_variables = list(set(constrained_variables))  # set and back to list for unique elements
      self._constrained_parameters_sorted = [p for p in self.all_parameters_sorted if p.name in constrained_variables]
      self._unconstrained_parameters = [p for p in self.all_parameters_sorted if p.name not in constrained_variables]
      self._halfspaces = parse_constraints_to_halfspaces(self.constraints, self.all_parameters)
      self._has_integer_constraints = any(p.is_integer for p in self.constrained_parameters)
    else:
      self._constrained_parameters_sorted = []
      self._unconstrained_parameters = self.all_parameters
      self._halfspaces = None
      self._has_integer_constraints = False

  @property
  def has_constraints(self):
    return bool(self.constraints)

  @property
  def all_metrics(self):
    return self.all_metrics_sorted

  @property
  def all_parameters(self):
    return self.all_parameters_sorted

  @property
  def all_parameters_including_deleted(self):
    return self._parameters

  @property
  def constrained_parameters(self):
    return self._constrained_parameters_sorted

  @property
  def unconstrained_parameters(self):
    return self._unconstrained_parameters

  @property
  def halfspaces(self):
    return self._halfspaces

  @property
  def has_integer_constraints(self):
    return self._has_integer_constraints


class Experiment(Base):
  # pylint: disable=too-many-public-methods

  NAME_MAX_LENGTH = 100
  CATEGORICAL_VALUE_MAX_LENGTH = 50
  CLIENT_PROVIDED_DATA_MAX_KEYS = 100
  CLIENT_PROVIDED_DATA_MAX_KEY_LENGTH = 100
  CLIENT_PROVIDED_DATA_MAX_LENGTH = 500

  __tablename__ = "experiments"

  id = Column(BigInteger, primary_key=True)
  client_id = Column(BigInteger, ForeignKey("clients.id"))
  project_id = Column(BigInteger)
  name = Column(String)
  date_created = Column(ImpliedUTCDateTime)
  experiment_meta = ProtobufColumn(
    ExperimentMeta,
    proxy=ExperimentMetaProxy,
    name="experiment_meta_json",
    nullable=False,
  )
  deleted = Column(Boolean, default=False)
  created_by = Column(BigInteger)
  date_updated = Column(ImpliedUTCDateTime)

  __table_args__ = (
    Index("c-e-index", "client_id", "id"),
    Index("c-u-e-index", "client_id", "created_by", "id"),
    Index("c-d-e-index", "client_id", "date_updated", "id"),
    ForeignKeyConstraint(
      ["project_id", "client_id"],
      ["projects.id", "projects.client_id"],
      ondelete="RESTRICT",
    ),
  )

  def __init__(self, *args, **kwargs):
    kwargs["experiment_meta"] = kwargs.get("experiment_meta", Experiment.experiment_meta.default_value())
    super().__init__(*args, **kwargs)

  @validates("experiment_meta", "_experiment_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=ExperimentMetaProxy)

  @property
  def runs_only(self):
    return self.experiment_meta.runs_only

  @property
  def all_parameters(self):
    return self.all_parameters_sorted

  @property
  def all_parameters_including_deleted(self):
    return self.experiment_meta.all_parameters_including_deleted

  @property
  def all_parameters_including_deleted_map(self):
    return self.experiment_meta.all_parameters_including_deleted_map

  @property
  def all_parameters_map(self):
    return self.experiment_meta.all_parameters_map

  @property
  def all_parameters_sorted(self):
    return self.experiment_meta.all_parameters_sorted

  @property
  def double_parameters_sorted(self):
    return self.experiment_meta.double_parameters_sorted

  @property
  def client_provided_data(self):
    return self.experiment_meta.GetFieldOrNone("client_provided_data")

  @property
  def client_provided_data_dict(self):
    client_provided_data = self.client_provided_data
    return json.loads(client_provided_data) if client_provided_data else {}

  @property
  def dimension(self):
    return len(self.all_parameters)

  @property
  def experiment_type(self):
    return self.experiment_meta.experiment_type or ExperimentMeta.OFFLINE

  @property
  def can_generate_fallback_suggestions(self):
    return self.experiment_type != ExperimentMeta.GRID

  @property
  def has_non_categorical_parameters(self):
    return any(not p.is_categorical for p in self.all_parameters)

  @property
  def has_constraints(self):
    return bool(self.constraints)

  @property
  def halfspaces(self):
    return self.experiment_meta.halfspaces

  @property
  def constrained_parameters(self):
    return self.experiment_meta.constrained_parameters

  @property
  def unconstrained_parameters(self):
    return self.experiment_meta.unconstrained_parameters

  @property
  def has_prior(self):
    return any(p.has_prior for p in self.all_parameters)

  @property
  def has_user_defined_metric(self):
    return self.experiment_meta.has_user_defined_metric

  @property
  def all_metrics(self):
    return self.experiment_meta.all_metrics

  @property
  def optimized_metrics(self):
    return [metric for metric in self.all_metrics if metric.is_optimized]

  @property
  def constraint_metrics(self):
    return [metric for metric in self.all_metrics if metric.is_constraint]

  @property
  def has_constraint_metrics(self):
    return any(metric.is_constraint for metric in self.all_metrics)

  @property
  def observation_budget(self):
    return self.experiment_meta.GetFieldOrNone("observation_budget")

  @property
  def should_offline_optimize(self):
    return self.experiment_type == ExperimentMeta.OFFLINE and self.has_non_categorical_parameters

  @property
  def is_multitask(self):
    return len(self.tasks) > 1

  @property
  def has_multiple_metrics(self):
    return len(self.all_metrics) > 1

  @property
  def requires_pareto_frontier_optimization(self):
    return len(self.optimized_metrics) > 1

  @property
  def metric_thresholds(self):
    return [metric.threshold for metric in self.all_metrics]

  @property
  def development(self):
    return bool(self.experiment_meta.development)

  @property
  def num_solutions(self):
    return self.experiment_meta.num_solutions

  @property
  def constraints(self):
    return self.experiment_meta.constraints

  @property
  def has_integer_constraints(self):
    return self.experiment_meta.has_integer_constraints

  @property
  def force_hitandrun_sampling(self):
    return self.experiment_meta.force_hitandrun_sampling

  @property
  def conditionals(self):
    return self.experiment_meta.conditionals

  @property
  def conditionals_breadth(self):
    return sum(len(c.values) for c in self.conditionals)

  @property
  def conditionals_map(self):
    return self.experiment_meta.conditionals_map

  @property
  def parallel_bandwidth(self):
    return self.experiment_meta.parallel_bandwidth

  @property
  def tasks(self):
    return self.experiment_meta.tasks

  @property
  def cheapest_task(self):
    return min_option(self.tasks, key=lambda x: x.cost)

  @property
  def costliest_task(self):
    return max_option(self.tasks, key=lambda x: x.cost)

  def get_task_by_name(self, task_name):
    matching_task = find(self.tasks, lambda t: t.name == task_name)
    if matching_task is None:
      raise ValueError(f"No task named {task_name} for experiment {self.id}.")
    return matching_task

  def get_task_by_cost(self, task_cost):
    matching_task = find(self.tasks, lambda t: t.cost == task_cost)
    if matching_task is None:
      raise ValueError(f"No task with cost {task_cost} for experiment {self.id}.")
    return matching_task

  @property
  def is_search(self):
    return len(self.optimized_metrics) == 0 and len(self.constraint_metrics) > 0

  @property
  def is_xgb(self):
    client_provided_data = self.experiment_meta.client_provided_data
    client_provided_data_dict = json.loads(client_provided_data) if client_provided_data else {}
    return "_IS_XGB_EXPERIMENT" in client_provided_data_dict
