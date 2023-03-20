# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.experiment.model import Experiment  # type: ignore
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentConditional  # type: ignore


def conditions_json(conditions: Sequence[ExperimentConditional], experiment: Experiment) -> dict[str, list]:
  json_dict: dict[str, list] = dict()
  for condition in conditions:
    json_dict[condition.name] = []
    try:
      conditional = experiment.conditionals_map[condition.name]
      all_conditional_values_map_by_index = to_map_by_key(conditional.values, lambda c: c.enum_index)
      for value in condition.values:
        conditional_value = all_conditional_values_map_by_index[value]
        json_dict[condition.name].append(conditional_value.name)
    except KeyError as e:
      raise Exception(f"Error serializing condition {condition.name} to json") from e
  return json_dict
