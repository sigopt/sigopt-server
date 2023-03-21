# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from sigoptlitetest.endpoints.base_test import UnitTestsEndpoint


class TestObservation(UnitTestsEndpoint):
  def test_create_observation_with_suggestion(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment = self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(experiment.id).suggestions().create()
    value = numpy.random.rand()
    observation = (
      self.conn.experiments(experiment.id)
      .observations()
      .create(suggestion=suggestion.id, values=[{"name": "y1", "value": value}])
    )
    assert observation.values[0].value == value
    assert observation.values[0].value_stddev is None
    assert observation.assignments == suggestion.assignments
