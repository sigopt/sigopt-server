# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Constants for calling compute; e.g., tolerances, variance, etc."""

# This quantity will be used in circumstances where there is insufficient data for reranking
# This quantity is functionally irrelevant, so long as it is >sqrt(MINIMUM_VALUE_VAR) to prevent exclusion
DEFAULT_EI_WHEN_UNCOMPUTABLE = 1.0
MINIMUM_SUCCESSES_TO_COMPUTE_EI = 3

# Minimum length-scale for integers. We want to select a value where
# sampling 1 and 2 would make values in (1, 2) uninteresting to compute without
# unduly influencing say further away points like 3, 4, 5, ...
# Scale = 0.01 means behavior returns to the prior quickly and compute will want to
# try useless points like 1.5. Scale = 10.0 would mean sampling 1 strongly
# influences 2, eliminating the possibility of a (nearly) independent integer parameter.
MINIMUM_INTEGER_LENGTH_SCALE = 0.5

# The minimum edge length for each dimension of the spatial/search domain,
# aka the domain we are optimizing over
# Tiny values lead to numerical difficulties.
MINIMUM_DOMAIN_EDGE_LENGTH = 1e-8

# Default choice for Gaussian process mean, either 'zero' or 'automatic'
# 'automatic' will activate constant mean after d points have been sampled
DEFAULT_NONZERO_MEAN = "automatic"

# If automatic nonzero mean is used, switch to turn on linear mean
# This replaces a constant after "enough" points (right now it's 3d points)
ACTIVATE_LINEAR_MEAN = False

# Activates the auto noise computation involving a regularization constant added to the diagonal
DEFAULT_AUTO_NOISE_ACTIVATED = False

DEFAULT_QEI_RERANKING_NUM_PADDING_SUGGESTIONS = 100
DEFAULT_QEI_RERANKING_MAX_POINTS_TO_EVALUATE = 100
DEFAULT_QEI_RERANKING_MAX_OPEN_SUGGESTIONS = 22
DEFAULT_QEI_RERANKING_MAX_OBSERVATIONS = 200


DEFAULT_CONSTRAINT_METRIC_QEI_RERANKING_MAX_OPEN_SUGGESTIONS = 5
DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OPEN_SUGGESTIONS = 5
DEFAULT_CONSTRAINT_METRIC_QEI_NEXT_POINTS_MAX_OBSERVATIONS = 200
