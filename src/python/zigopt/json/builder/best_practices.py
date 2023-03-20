# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field


class BestPracticesJsonBuilder(JsonBuilder):
  object_name = "best_practices"

  def __init__(self, violations: Sequence[str]):
    self._violations = violations

  @field(ValidationType.arrayOf(ValidationType.string))
  def violations(self) -> Sequence[str]:
    return self._violations
