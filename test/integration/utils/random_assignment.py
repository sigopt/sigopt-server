# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random


def rand_param(param):
  if param.type == "int":
    return random.randint(int(param.bounds.min), int(param.bounds.max))
  if param.type == "double":
    return random.uniform(param.bounds.min, param.bounds.max)
  if param.type == "categorical":
    return random.choice([c.name for c in param.categorical_values])
  raise Exception(f"Unknown parameter type {param.type}!")


def random_assignments(exp):
  return {p.name: rand_param(p) for p in exp.parameters}
