# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random


def make_values(exp, val=None):
  if isinstance(val, (int, float)):
    vals = [val for _ in exp.metrics]
  elif val is not None:
    vals = val
  else:
    vals = [random.random() for _ in exp.metrics]
  return [{"name": m.name, "value": v} for (m, v) in zip(exp.metrics, vals)]
