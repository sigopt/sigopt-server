# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.json.builder import StoppingCriteriaJsonBuilder


class TestStoppingCriteriaJsonBuilder:
  @pytest.mark.parametrize(
    "possible_stagnation,observation_budget_reached",
    [
      (False, False),
      (False, True),
      (True, False),
      (True, True),
    ],
  )
  def test_stopping_criteria(self, possible_stagnation, observation_budget_reached):
    sc_json = StoppingCriteriaJsonBuilder.json(possible_stagnation, observation_budget_reached)
    assert set(sc_json.keys()) == set(["should_stop", "reasons", "object"])
    assert possible_stagnation == ("possible_stagnation" in sc_json.get("reasons"))
    assert observation_budget_reached == ("observation_budget_reached" in sc_json.get("reasons"))
    assert (possible_stagnation or observation_budget_reached) == sc_json.get("should_stop")
