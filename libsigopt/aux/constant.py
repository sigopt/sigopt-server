# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
#: The minimum value_var/noise variance we are allowed to pass to libsigopt.compute.
#: This is for numerical stability reasons--avoiding singular matrix errors
#: by making the data "slightly wrong."
# NOTE: If this is for numerical issues, we should reconsider it in the context of the more stable
# methods that we have available now.
MINIMUM_VALUE_VAR = 1.0e-10

# Mechanism for determining
TASK_SELECTION_STRATEGY_MAX_AF = "max_af"
TASK_SELECTION_STRATEGY_A_PRIORI = "a_priori"
DEFAULT_TASK_SELECTION_STRATEGY = TASK_SELECTION_STRATEGY_A_PRIORI

#: experiment parameter types
DOUBLE_EXPERIMENT_PARAMETER_NAME = "double"
INT_EXPERIMENT_PARAMETER_NAME = "int"
CATEGORICAL_EXPERIMENT_PARAMETER_NAME = "categorical"
QUANTIZED_EXPERIMENT_PARAMETER_NAME = "quantized"

# GP Parallelism strategy
PARALLEL_CONSTANT_LIAR = "constant_liar"
PARALLEL_QEI = "qei"


class ParameterPriorNames(object):
  NORMAL = "normal"
  BETA = "beta"


class ParameterTransformationNames(object):
  NONE = "none"
  LOG = "log"


class ConstraintType(object):
  greater_than = "greater_than"
  less_than = "less_than"


# Threshold for number of observations beyond which we use SPE rather than GP to compute next points
# The cutoff at scoring could be made higher than 600, as the actual computation isn't very slow
# This is chosen to prevent SuggestionCreate from having to grab increasingly large chunks of data
# which will slow the API return time, which is important for the server solution
DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS = 600
DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS = 50
DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS_WITH_CONSTRAINTS = 20

#: We enforce that the metric values will range over [-M, M] using the "midpoint" normalization.
#: This is computed on previous data. So we select alpha assuming that ~80% of the
#: prior distribution falls within that range.
#: Note: added some randomness b/c I observed strange effects when historical data is centered
#:   about exact multiples of the default alpha.
# TODO(RTL-140): for experiments with lots of data, we could estimate this the same way
#   we estimate the hyperparameter domain
DEFAULT_HYPERPARAMETER_ALPHA = 0.0803280478237
DEFAULT_HYPERPARAMETER_TIKHONOV = 1e-3

# Obviously this should be covariance dependent but it will do for now.
DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE = 0.18

# Maximum number of simultaneous EI computations to allow during next points search
MAX_SIMULTANEOUS_AF_POINTS = 1000

# Multisolution quantile for creating the threshold in search next points
MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD = 0.8
MULTISOLUTION_TOP_OBSERVATIONS_FRACTION = 1 - MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD

MAX_NUM_INT_CONSTRAINT_VARIABLES = 10
