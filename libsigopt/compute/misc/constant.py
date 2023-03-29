# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

# Covariance type names
SQUARE_EXPONENTIAL_COVARIANCE_TYPE = "square_exponential"
C4_RADIAL_MATERN_COVARIANCE_TYPE = "c4_radial_matern"
C2_RADIAL_MATERN_COVARIANCE_TYPE = "c2_radial_matern"
C0_RADIAL_MATERN_COVARIANCE_TYPE = "c0_radial_matern"

#: Covariance types supported
COVARIANCE_TYPES = [
  SQUARE_EXPONENTIAL_COVARIANCE_TYPE,
  C4_RADIAL_MATERN_COVARIANCE_TYPE,
  C2_RADIAL_MATERN_COVARIANCE_TYPE,
  C0_RADIAL_MATERN_COVARIANCE_TYPE,
]

DEFAULT_COVARIANCE_KERNEL = C4_RADIAL_MATERN_COVARIANCE_TYPE
DEFAULT_TASK_COVARIANCE_KERNEL = SQUARE_EXPONENTIAL_COVARIANCE_TYPE

# Nonzero mean names (yes, zero is an acceptable nonzero mean)
NONZERO_MEAN_ZERO_MEAN_TYPE = "zero"
NONZERO_MEAN_CONSTANT_MEAN_TYPE = "constant"
NONZERO_MEAN_LINEAR_MEAN_TYPE = "linear"
NONZERO_MEAN_CUSTOM_MEAN_TYPE = "custom"

#: Nonzero mean types which can be passed by SigOpt
#   A more diverse selection is available within libsigopt.compute itself, but we restrict this to strings only
NONZERO_MEAN_TYPES = [
  NONZERO_MEAN_ZERO_MEAN_TYPE,
  NONZERO_MEAN_CONSTANT_MEAN_TYPE,
  NONZERO_MEAN_LINEAR_MEAN_TYPE,
  NONZERO_MEAN_CUSTOM_MEAN_TYPE,
]

# Optimizer constants
L_BFGS_B_OPTIMIZER = "l_bfgs_b_optimizer"
SLSQP_OPTIMIZER = "slsqp_optimizer"

# Vectorized Optimizer names
ADAM_OPTIMIZER = "adam"
DE_OPTIMIZER = "differential evolution"

# Vectorized optimizer types
GRADIENT_BASED_OPTIMIZERS = [
  ADAM_OPTIMIZER,
]

EVOLUTIONARY_STRATEGY_OPTIMIZERS = [
  DE_OPTIMIZER,
]

# Constant Liar constants
CONSTANT_LIAR_MIN = "constant_liar_min"
CONSTANT_LIAR_MAX = "constant_liar_max"
CONSTANT_LIAR_MEAN = "constant_liar_mean"

DEFAULT_CONSTANT_LIAR_VALUE = -0.0123456789  # In the event there is no data (should crash maybe??)

# TODO(GH-257): Find a better default.
DEFAULT_CONSTANT_LIAR_LIE_NOISE_VARIANCE = 1e-12

AF_OPT_NEAR_BEST_STD_DEV = 0.01

DEFAULT_MAX_SIMULTANEOUS_EI_POINTS = 10000
DEFAULT_MAX_SIMULTANEOUS_QEI_POINTS = 100

CATEGORICAL_POINT_UNIQUENESS_TOLERANCE = 1e-2
DISCRETE_UNIQUENESS_LENGTH_SCALE_MIN_BOUND = {
  SQUARE_EXPONENTIAL_COVARIANCE_TYPE: 0.5,
  C4_RADIAL_MATERN_COVARIANCE_TYPE: 0.14,
  C2_RADIAL_MATERN_COVARIANCE_TYPE: 0.18,
  C0_RADIAL_MATERN_COVARIANCE_TYPE: 0.25,
}
TASK_LENGTH_LOWER_BOUND = 0.43
QUANTIZED_LENGTH_SCALE_LOWER_FACTOR = 0.25

# In multimetric (only applied to epsilon constraint or probabilistic failures),
# we enforce a min amount of successful points so that it can't return all failures.
MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS = 5
MULTIMETRIC_MIN_NUM_IN_BOUNDS_POINTS = 1
