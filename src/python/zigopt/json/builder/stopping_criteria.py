# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field


class StoppingCriteriaJsonBuilder(JsonBuilder):
  object_name = "stopping_criteria"

  def __init__(self, possible_stagnation: bool, observation_budget_reached: bool):
    self._reasons = []
    if possible_stagnation:
      self._reasons.append("possible_stagnation")
    if observation_budget_reached:
      self._reasons.append("observation_budget_reached")

  @field(ValidationType.boolean)
  def should_stop(self) -> bool:
    return len(self._reasons) > 0

  @field(ValidationType.arrayOf(ValidationType.string))
  def reasons(self) -> list[str]:
    return self._reasons
