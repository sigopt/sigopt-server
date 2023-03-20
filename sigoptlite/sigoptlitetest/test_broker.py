# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from sigoptlite.broker import Broker
from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.driver import dataclass_to_dict
from sigoptlitetest.base_test import UnitTestsBase


class TestBroker(UnitTestsBase):
  @pytest.mark.parametrize("num_observations", [1])
  def test_basic(self, experiment_meta, num_observations):
    experiment = LocalExperimentBuilder(experiment_meta)
    broker = Broker(experiment)
    for _ in range(num_observations):
      suggestion = broker.create_suggestion()
      self.assert_valid_suggestion(suggestion, experiment)

      local_observation = self.make_random_observation(experiment, suggestion=suggestion)
      assignments_dict = local_observation.assignments
      values_dicts = [dataclass_to_dict(v) for v in local_observation.values] if local_observation.values else None
      task_dict = dataclass_to_dict(local_observation.task) if local_observation.task else None

      broker.create_observation(
        assignments=assignments_dict,
        values=values_dicts,
        failed=local_observation.failed,
        task=task_dict,
      )
