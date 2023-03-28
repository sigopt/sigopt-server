# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import pytest
from libsigopt.aux.constant import DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS
from mock import Mock, patch

from zigopt.observation.model import Observation, ObservationDataProxy
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.sigoptcompute.constant import MINIMUM_SUCCESSES_TO_COMPUTE_EI
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.optimize.optimizer.test_base import OptimizerServiceTestBase
from integration.utils.constants import EXPECTED_GP_OPTIMIZATION_SOURCE


class TestTriggerNextPoints(OptimizerServiceTestBase):
  @pytest.mark.slow
  def test_spe_many_observations(self, services, experiment):
    with patch.object(services.optimizer, "persist_suggestions", new_callable=Mock):
      observation_datas = [
        ObservationData(
          values=[ObservationValue(value=random.random())], assignments_map=dict(p1=random.uniform(-10, 10))
        )
        for _ in range(DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS + 1)
      ]
      observations = [
        Observation(
          data=ObservationDataProxy(data),
          experiment_id=experiment.id,
        )
        for data in observation_datas
      ]
      services.observation_service.insert_observations(experiment, observations)
      services.optimizer.trigger_next_points(experiment)
      ((_, suggestions), _) = services.optimizer.persist_suggestions.call_args
      assert len(suggestions) > 0
      assert all(s.source == UnprocessedSuggestion.Source.SPE for s in suggestions) is True

  def test_spe_high_dimension_no_observations(self, services, experiment_high_dimension):
    experiment = experiment_high_dimension
    with patch.object(services.optimizer, "persist_suggestions", new_callable=Mock):
      services.optimizer.trigger_next_points(experiment)
      ((_, suggestions), _) = services.optimizer.persist_suggestions.call_args
      assert len(suggestions) == 0

  def test_categorical_no_observations(self, services, experiment):
    with patch.object(services.optimizer, "persist_suggestions", new_callable=Mock):
      services.optimizer.trigger_next_points(experiment)
      ((_, suggestions), _) = services.optimizer.persist_suggestions.call_args
      assert len(suggestions) == 0

  def test_gp_source(self, services, experiment):
    # Note: This is the most expensive test in this file
    with patch.object(services.optimizer, "persist_suggestions", new_callable=Mock):
      observations = []
      for _ in range(MINIMUM_SUCCESSES_TO_COMPUTE_EI):
        observation_data = ObservationData(
          values=[ObservationValue(value=random.random())], assignments_map=dict(p1=random.uniform(-10, 10))
        )
        observations.append(
          Observation(
            data=ObservationDataProxy(observation_data),
            experiment_id=experiment.id,
          )
        )
      services.observation_service.insert_observations(experiment, observations)
      services.optimizer.trigger_next_points(experiment)
      ((_, suggestions), _) = services.optimizer.persist_suggestions.call_args
      assert len(suggestions) > 0
      assert all(s.source == EXPECTED_GP_OPTIMIZATION_SOURCE for s in suggestions) is True
