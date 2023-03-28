# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.sigoptaux.constant import DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS

from zigopt.common import *
from zigopt.experiment.constant import MetricStrategyNames
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.optimize.sources.conditional import ConditionalOptimizationSource
from zigopt.optimize.sources.spe import SPEOptimizationSource


def source_class_from_experiment_meta(experiment_meta):
  if experiment_meta.conditionals:
    return ConditionalOptimizationSource
  elif len(experiment_meta.all_parameters_sorted) >= DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS:
    return SPEOptimizationSource
  else:
    return CategoricalOptimizationSource


def group_metric_strategies_from_json(metric_list_json):
  return as_grouped_dict(
    metric_list_json,
    lambda metric: (
      # NOTE: users can specify just a metric string (name) rather than an object, which defaults to OPTIMIZE
      MetricStrategyNames.OPTIMIZE
      if is_string(metric)
      else metric.get("strategy", MetricStrategyNames.OPTIMIZE)
    ),
  )


def get_experiment_default_metric_name(experiment):
  if experiment.is_search:
    return experiment.constraint_metrics[0].name
  return experiment.optimized_metrics[0].name
