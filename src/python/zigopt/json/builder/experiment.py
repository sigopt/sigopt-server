# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Literal, Optional

from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.experiment.constant import (
  EXPERIMENT_TYPE_TO_NAME,
  METRIC_OBJECTIVE_TYPE_TO_NAME,
  METRIC_STRATEGY_TYPE_TO_NAME,
)
from zigopt.experiment.model import Experiment, ExperimentMetaProxy
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.observation import ObservationJsonBuilder
from zigopt.json.builder.parameter import ExperimentParameterJsonBuilder
from zigopt.json.builder.task import TaskJsonBuilder
from zigopt.json.client_provided_data import client_provided_data_json
from zigopt.project.model import Project
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  ExperimentConditional,
  ExperimentConstraint,
  ExperimentMetric,
  Term,
)


class ConditionalJsonBuilder(JsonBuilder):
  object_name = "conditional"

  def __init__(self, conditional: ExperimentConditional):
    self._conditional = conditional

  @field(ValidationType.string)
  def name(self) -> str:
    return self._conditional.name

  @field(ValidationType.arrayOf(ValidationType.oneOf([ValidationType.string, ValidationType.none])))
  def values(self) -> list[str]:
    return [c.name for c in self._conditional.values]


class ConstraintTermJsonBuilder(JsonBuilder):
  object_name = "constraint_term"

  def __init__(self, term: Term):
    self._term = term

  @field(ValidationType.string)
  def name(self) -> str:
    return self._term.name

  @field(ValidationType.number)
  def weight(self) -> float:
    return self._term.coeff


class ConstraintJsonBuilder(JsonBuilder):
  object_name = "linear_constraint"

  def __init__(self, constraint: ExperimentConstraint):
    self._constraint = constraint

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def terms(self) -> list[ConstraintTermJsonBuilder]:
    return [
      ConstraintTermJsonBuilder(a)
      for a in sorted(
        self._constraint.terms,
        key=lambda term: term.name.lower(),
      )
    ]

  @field(ValidationType.number)
  def threshold(self) -> float:
    return self._constraint.rhs

  @field(ValidationType.string)
  def type(self) -> str:
    return self._constraint.type


class MetricJsonBuilder(JsonBuilder):
  object_name = "metric"

  def __init__(self, metric: ExperimentMetric):
    self._metric = metric

  @field(ValidationType.string)
  def name(self) -> Optional[str]:
    if len(self._metric.name):
      return self._metric.name
    return None

  @field(ValidationType.string)
  def objective(self) -> str:
    return METRIC_OBJECTIVE_TYPE_TO_NAME[self._metric.objective]

  @field(ValidationType.number)
  def threshold(self) -> Optional[float]:
    return self._metric.threshold if self._metric.HasField("threshold") else None

  @field(ValidationType.string)
  def strategy(self) -> str:
    return METRIC_STRATEGY_TYPE_TO_NAME[self._metric.strategy]


class ObservationProgressJsonBuilder(JsonBuilder):
  object_name = "progress"

  def __init__(self, experiment: Experiment, progress: Any):
    assert experiment is not None
    self._experiment = experiment
    self._progress = progress

  @field(ValidationType.non_negative_integer)
  def observation_count(self) -> int:
    return self._pattr("count", default=0)

  @field(ValidationType.non_negative_number)
  def observation_budget_consumed(self) -> int:
    return self._pattr("observation_budget_consumed", default=0)

  @field(JsonBuilderValidationType())
  def first_observation(self) -> Optional[ObservationJsonBuilder]:
    return self._observation("status_quo")

  @field(JsonBuilderValidationType())
  def last_observation(self) -> Optional[ObservationJsonBuilder]:
    return self._observation("last_observation")

  @field(JsonBuilderValidationType())
  def best_observation(self) -> Optional[ObservationJsonBuilder]:
    # Only show best observations for single metric experiments
    if len(self._experiment.optimized_metrics) == 1:
      return self._observation("best_observation")
    return None

  def _pattr(self, attr: str, default: Any = None) -> Any:
    value = napply(self._progress, lambda p: getattr(p, attr, None))  # type: ignore
    return coalesce(value, default)

  def _observation(self, attr: str) -> Optional[ObservationJsonBuilder]:
    if (obs := self._pattr(attr)) is not None:
      return ObservationJsonBuilder(self._experiment, obs)
    return None


class RunProgressJsonBuilder(JsonBuilder):
  object_name = "progress"

  def __init__(self, experiment: Experiment, progress: Any):
    assert experiment is not None
    assert progress is not None
    self._experiment = experiment
    self._progress = progress

  @field(ValidationType.non_negative_integer)
  def finished_run_count(self) -> int:
    return self._progress.finished_run_count

  @field(ValidationType.non_negative_integer)
  def active_run_count(self) -> int:
    return self._progress.active_run_count

  @field(ValidationType.non_negative_integer)
  def total_run_count(self) -> int:
    return self.active_run_count() + self.finished_run_count()

  @field(ValidationType.number)
  def remaining_budget(self) -> Optional[float]:
    if self._experiment.observation_budget is None:
      return None
    return self._experiment.observation_budget - self.total_run_count()


class ExperimentJsonBuilder(JsonBuilder):
  # pylint: disable=too-many-public-methods
  object_name = "experiment"

  def __init__(
    self,
    experiment: Experiment,
    progress_builder: Optional[JsonBuilder] = None,
    project: Optional[Project] = None,
    auth: Optional[EmptyAuthorization] = None,
  ):
    self._experiment = experiment
    self._progress_builder = progress_builder
    self._project = project
    self._auth = auth

  @field(ValidationType.id)
  def client(self) -> int:
    return self._experiment.client_id

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._experiment.date_created, datetime_to_seconds)

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def conditionals(self) -> list[ConditionalJsonBuilder]:
    return [ConditionalJsonBuilder(c) for c in self._experiment.conditionals]

  @field(ValidationType.boolean)
  def development(self) -> bool:
    return self._experiment.development

  @field(ValidationType.id)
  def id(self) -> int:
    return self._experiment.id

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def linear_constraints(self) -> list[ConstraintJsonBuilder]:
    return [ConstraintJsonBuilder(c) for c in self._experiment.constraints]

  @field(ValidationType.object)
  def metadata(self) -> Optional[dict]:
    return napply(self._experiment.client_provided_data, client_provided_data_json)

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def metrics(self) -> list[MetricJsonBuilder]:
    return [MetricJsonBuilder(m) for m in sorted(self._experiment.all_metrics, key=lambda m: m.name)]

  @field(ValidationType.string)
  def name(self) -> str:
    return self._experiment.name

  @property
  def meta(self) -> ExperimentMetaProxy:
    return self._experiment.experiment_meta

  @field(ValidationType.positive_integer)
  def num_solutions(self) -> Optional[int]:
    if self.meta.HasField("num_solutions"):
      return self.meta.num_solutions
    return None

  def hide_observation_budget(self) -> bool:
    return self._experiment.runs_only

  @field(ValidationType.positive_integer, hide=hide_observation_budget)
  def observation_budget(self) -> Optional[int]:
    return self._experiment.observation_budget

  def hide_budget(self) -> bool:
    return not self._experiment.runs_only

  @field(ValidationType.positive_integer, hide=hide_budget)
  def budget(self) -> Optional[int]:
    return self._experiment.observation_budget

  @field(ValidationType.positive_integer)
  def parallel_bandwidth(self) -> Optional[int]:
    if self.meta.HasField("parallel_bandwidth"):
      return self.meta.parallel_bandwidth
    return None

  @field(ValidationType.string)
  def project(self) -> Optional[str]:
    return napply(self._project, lambda p: p.reference_id)

  @field(ValidationType.string)
  def state(self) -> Literal["active", "deleted"]:
    return "deleted" if self._experiment.deleted else "active"

  @field(ValidationType.string)
  def type(self) -> str:
    return EXPERIMENT_TYPE_TO_NAME[self._experiment.experiment_type]

  @field(ValidationType.integer)
  def updated(self) -> Optional[float]:
    return napply(self._experiment.date_updated, datetime_to_seconds)

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._experiment.created_by

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def parameters(self) -> list[ExperimentParameterJsonBuilder]:
    return [ExperimentParameterJsonBuilder(param, self._experiment) for param in self._experiment.all_parameters_sorted]

  @field(JsonBuilderValidationType())
  def progress(self) -> Optional[JsonBuilder]:
    return self._progress_builder

  def hide_tasks(self) -> bool:
    return not self._experiment.is_multitask

  @field(ValidationType.arrayOf(JsonBuilderValidationType()), hide=hide_tasks)
  def tasks(self) -> list[TaskJsonBuilder]:
    return [TaskJsonBuilder(task) for task in sorted(self._experiment.tasks, key=lambda x: x.cost, reverse=True)]

  @field(ValidationType.boolean)
  def runs_only(self) -> bool:
    return self._experiment.runs_only
