# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from sigoptlite.broker import Broker
from sigoptlite.builders import LocalExperimentBuilder
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
      observation_dict = local_observation.get_client_observation(experiment)
      broker.create_observation(**observation_dict)
