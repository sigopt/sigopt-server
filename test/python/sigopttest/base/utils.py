# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.optimize.args import OptimizationArgs


@generator_to_safe_iterator
def generate_ids():
  i = 1
  while True:
    yield i
    i += 1


def partial_opt_args(**kwargs):
  args = OptimizationArgs(
    failure_count=0,
    max_observation_id=0,
    observation_count=0,
    observation_iterator=iter([]),
    old_hyperparameters=None,
    open_suggestions=[],
    source=None,  # type: ignore
    last_observation=None,
  )
  return args.copy_and_set(**kwargs)
