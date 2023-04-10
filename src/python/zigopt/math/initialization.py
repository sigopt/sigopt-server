# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.conditionals.util import convert_to_unconditioned_experiment


def get_low_discrepancy_stencil_length_from_experiment(experiment):
  if experiment.conditionals:
    experiment = convert_to_unconditioned_experiment(experiment)
  categorical_parameters, numeric_parameters = partition(
    experiment.all_parameters,
    lambda p: p.is_categorical,
  )
  num_categories = sum(len(p.active_categorical_values) for p in categorical_parameters)
  stencil_length = max(num_categories, 1) * len(numeric_parameters)

  stencil_length += experiment.parallel_bandwidth - 1
  # For very high parallel bandwidth, allow for higher stencil length
  stencil_length = min(stencil_length, 100 + experiment.parallel_bandwidth - 1)
  stencil_length = max(stencil_length, 4)
  return stencil_length
