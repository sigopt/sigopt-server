# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import dataclass

import numpy


@dataclass(slots=True)
class PointsContainer:
  points: numpy.ndarray
  values: numpy.ndarray = None
  value_vars: numpy.ndarray = None
  failures: numpy.ndarray = None
  task_costs: numpy.ndarray = None


@dataclass(slots=True)
class DomainInfo:
  constraint_list: list
  domain_components: list = None
  force_hitandrun_sampling: bool = False
  priors: list = None

  @property
  def dim(self) -> int:
    return len(self.domain_components)


@dataclass(slots=True)
class MetricsInfo:
  requires_pareto_frontier_optimization: bool
  observation_budget: int
  user_specified_thresholds: list
  objectives: list
  optimized_metrics_index: list
  constraint_metrics_index: list

  @property
  def has_optimization_metrics(self):
    return len(self.optimized_metrics_index) > 0

  @property
  def has_constraint_metrics(self):
    return len(self.constraint_metrics_index) > 0

  @property
  def has_optimized_metric_thresholds(self):
    if len(self.optimized_metrics_index) == 0:
      return False
    return any(self.user_specified_thresholds[i] is not None for i in self.optimized_metrics_index)


@dataclass(slots=True)
class GPModelInfo:
  hyperparameters: list[dict]
  max_simultaneous_af_points: int
  nonzero_mean_info: dict
  task_selection_strategy: str = None
