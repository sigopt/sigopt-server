# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Constants for ``sigopt-server`` experiment components."""
from zigopt.common import *
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  MAXIMIZE,
  MINIMIZE,
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentMetric,
  ExperimentParameter,
  Prior,
)

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
  ParameterTransformationNames,
)


#: mapping of string names to (protobuf) enumerated experiment parameter types
EXPERIMENT_PARAMETER_NAME_TO_TYPE, EXPERIMENT_PARAMETER_TYPE_TO_NAME = generate_constant_map_and_inverse(
  {
    DOUBLE_EXPERIMENT_PARAMETER_NAME: PARAMETER_DOUBLE,
    INT_EXPERIMENT_PARAMETER_NAME: PARAMETER_INT,
    CATEGORICAL_EXPERIMENT_PARAMETER_NAME: PARAMETER_CATEGORICAL,
  }
)

EXPERIMENT_NAME_TO_TYPE, EXPERIMENT_TYPE_TO_NAME = generate_constant_map_and_inverse(
  {
    "grid": ExperimentMeta.GRID,
    "offline": ExperimentMeta.OFFLINE,
    "random": ExperimentMeta.RANDOM,
  }
)


METRIC_OBJECTIVE_NAME_TO_TYPE, METRIC_OBJECTIVE_TYPE_TO_NAME = generate_constant_map_and_inverse(
  {
    "maximize": MAXIMIZE,
    "minimize": MINIMIZE,
  }
)

ALL_METRIC_OBJECTIVE_NAMES = list(METRIC_OBJECTIVE_NAME_TO_TYPE.keys())


class MetricStrategyNames:
  OPTIMIZE = "optimize"
  STORE = "store"
  CONSTRAINT = "constraint"


METRIC_STRATEGY_NAME_TO_TYPE, METRIC_STRATEGY_TYPE_TO_NAME = generate_constant_map_and_inverse(
  {
    MetricStrategyNames.OPTIMIZE: ExperimentMetric.OPTIMIZE,
    MetricStrategyNames.STORE: ExperimentMetric.STORE,
    MetricStrategyNames.CONSTRAINT: ExperimentMetric.CONSTRAINT,
  }
)
ALL_METRIC_STRATEGY_NAMES = list(METRIC_STRATEGY_NAME_TO_TYPE.keys())

MAX_OPTIMIZED_METRICS = 2
MAX_CONSTRAINT_METRICS = 4
MAX_METRICS_ANY_STRATEGY = 50

PARAMETER_PRIOR_NAME_TO_TYPE = {
  ParameterPriorNames.NORMAL: Prior.NORMAL,
  ParameterPriorNames.BETA: Prior.BETA,
}
ALL_PARAMETER_PRIOR_NAMES = list(PARAMETER_PRIOR_NAME_TO_TYPE.keys())

PARAMETER_TRANSFORMATION_NAME_TO_TYPE, PARAMETER_TRANSFORMATION_TYPE_TO_NAME = generate_constant_map_and_inverse(
  {
    ParameterTransformationNames.NONE: ExperimentParameter.TRANSFORMATION_NONE,
    ParameterTransformationNames.LOG: ExperimentParameter.TRANSFORMATION_LOG,
  }
)
