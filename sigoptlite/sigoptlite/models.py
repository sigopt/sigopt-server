# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import asdict, dataclass, field
from typing import List

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)


FIXED_EXPERIMENT_ID = "-1"


def dataclass_to_dict(obj):
  return asdict(obj)


def parameter_conditions_satisfied(parameter, assignments_map):
  if parameter.conditions:
    for condition in parameter.conditions:
      assignment = assignments_map.get(condition.name)
      if assignment is not None and assignment not in condition.values:
        return False
  return True


def replacement_value_if_missing(p):
  if p.is_categorical:
    return p.categorical_values[-1].name
  elif p.grid:
    return p.grid[-1]
  return p.bounds.max


@dataclass(frozen=True, kw_only=True)
class LocalCategoricalValue:
  enum_index: int
  name: str


@dataclass(frozen=True, kw_only=True)
class LocalConditionalValue:
  enum_index: int
  name: str


@dataclass(frozen=True, kw_only=True)
class LocalCondition:
  name: str
  values: List[str]


@dataclass(frozen=True, kw_only=True)
class LocalBounds:
  min: float
  max: float

  def is_value_within(self, value):
    return self.min <= value <= self.max


@dataclass(frozen=True, kw_only=True)
class LocalTask:
  name: str
  cost: float


@dataclass(frozen=True, kw_only=True)
class LocalParameterPrior:
  name: str
  mean: float = None
  scale: float = None
  shape_a: float = None
  shape_b: float = None

  @property
  def is_beta(self):
    return self.name == ParameterPriorNames.BETA

  @property
  def is_normal(self):
    return self.name == ParameterPriorNames.NORMAL


@dataclass(frozen=True, kw_only=True)
class LocalParameter:
  name: str
  type: str
  bounds: LocalBounds = None
  categorical_values: List[LocalCategoricalValue] = field(default_factory=list)
  conditions: List[LocalCondition] = field(default_factory=list)
  grid: List[float] = field(default_factory=list)
  prior: LocalParameterPrior = None
  transformation: str = None

  @property
  def is_categorical(self):
    return self.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME

  @property
  def is_double(self):
    return self.type == DOUBLE_EXPERIMENT_PARAMETER_NAME

  @property
  def has_prior(self):
    return self.prior is not None

  @property
  def has_transformation(self):
    return self.transformation is not None


@dataclass(frozen=True, kw_only=True)
class LocalConditional:
  name: str
  values: List[LocalConditionalValue]


@dataclass(frozen=True, kw_only=True)
class LocalConstraintTerm:
  name: str
  weight: float


@dataclass(frozen=True, kw_only=True)
class LocalLinearConstraint:
  terms: List[LocalConstraintTerm]
  threshold: float
  type: str


@dataclass(frozen=True, kw_only=True)
class LocalMetric:
  name: str
  objective: str = "maximize"
  strategy: str = "optimize"
  threshold: float = None

  @property
  def is_optimized(self):
    return self.strategy == "optimize"

  @property
  def is_constraint(self):
    return self.strategy == "constraint"

  @property
  def is_minimized(self):
    return self.objective == "minimize"


@dataclass(frozen=True, kw_only=True)
class LocalExperiment:
  id: str = FIXED_EXPERIMENT_ID
  parameters: List[LocalParameter]
  metrics: List[LocalMetric]
  conditionals: List[LocalConditional] = field(default_factory=list)
  linear_constraints: List[LocalLinearConstraint] = field(default_factory=list)
  metadata = None
  name: str = None
  num_solutions: int = 1
  observation_budget: int = None
  parallel_bandwidth: int = 1
  tasks: List[LocalTask] = field(default_factory=list)
  type: str = "offline"

  @property
  def dimension(self):
    return len(self.parameters)

  @property
  def num_metrics(self):
    return len(self.metrics)

  @property
  def optimized_metrics(self):
    return [m for m in self.metrics if m.is_optimized]

  @property
  def constraint_metrics(self):
    return [m for m in self.metrics if m.is_constraint]

  @property
  def requires_pareto_frontier_optimization(self):
    return len(self.optimized_metrics) > 1

  @property
  def is_multitask(self):
    return len(self.tasks) > 0

  @property
  def is_conditional(self):
    return len(self.conditionals) > 0

  @property
  def is_search(self):
    return len(self.optimized_metrics) == 0 and len(self.constraint_metrics) > 0

  @property
  def is_multisolution(self):
    return self.num_solutions > 1

  @property
  def is_random(self):
    return self.type == "random"

  @property
  def has_constraint_metrics(self):
    return any(metric.is_constraint for metric in self.metrics)


class LocalAssignments(dict):
  pass


@dataclass(frozen=True, kw_only=True)
class MetricEvaluation:
  name: str
  value: float
  value_stddev: float = None


@dataclass(frozen=True, kw_only=True)
class LocalObservation:
  assignments: LocalAssignments
  metric_evaluations: dict = field(default_factory=dict)
  failed: bool = False
  task: LocalTask = None

  def get_client_observation(self, experiment):
    return dict(
      assignments=dict(self.assignments),
      values=None if self.failed else [dataclass_to_dict(me) for me in self.get_metric_evaluations(experiment)],
      task=dataclass_to_dict(self.task) if self.task else None,
      failed=self.failed,
    )

  def get_metric_evaluations(self, experiment):
    return [self.get_metric_evaluation_by_name(m.name) for m in experiment.metrics]

  def get_metric_evaluation_by_name(self, metric_name):
    return self.metric_evaluations.get(metric_name)

  def get_optimized_measurements_for_maximization(self, experiment):
    return [self.get_value_for_maximization(metric) for metric in experiment.optimized_metrics]

  def get_value_for_maximization(self, metric):
    value = self.get_metric_evaluation_by_name(metric.name).value
    if value is None:
      raise Exception(f"Metric `{metric.name}` is not in observation data.")
    if metric.is_minimized:
      return -value
    return value

  def within_metric_threshold(self, metric, metric_evaluation):
    if metric.threshold is None:
      return True
    if metric.objective == "minimize":
      return metric_evaluation.value <= metric.threshold
    return metric_evaluation.value >= metric.threshold

  def within_metric_thresholds(self, experiment):
    return all(
      self.within_metric_threshold(metric, self.get_metric_evaluation_by_name(metric.name))
      for metric in experiment.metrics
    )


@dataclass(frozen=True, kw_only=True)
class LocalSuggestion:
  assignments: LocalAssignments
  id: str = None
  task: LocalTask = None

  def __post_init__(self):
    object.__setattr__(self, "assignments", LocalAssignments(self.assignments))

  def get_assignments(self, experiment):
    parameters = experiment.parameters
    conditionals = experiment.conditionals
    all_assignments_map = self._get_assignments_from_list(parameters + conditionals)
    assignments = dict(
      (p.name, all_assignments_map[p.name])
      for p in parameters
      if parameter_conditions_satisfied(p, all_assignments_map)
    )
    if experiment.conditionals:
      conditional_assignments = self._get_assignments_from_list(experiment.conditionals)
      assignments.update(conditional_assignments)
    return dict(assignments.items())

  def _get_assignments_from_list(self, list_of_keys):
    values = [self.assignments.get(k.name) for k in list_of_keys]
    return dict((k.name, value) for (k, value) in zip(list_of_keys, values))
