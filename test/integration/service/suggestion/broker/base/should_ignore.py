# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


class TestShouldIgnore(SuggestionBrokerTestBase):
  @pytest.mark.parametrize(
    "experiment_type",
    [
      ExperimentMeta.OFFLINE,
      ExperimentMeta.RANDOM,
      ExperimentMeta.GRID,
    ],
  )
  def test_no_observations(self, services, experiment_type):
    experiment_meta = self.new_experiment_meta(experiment_type=experiment_type)
    experiment = self.new_experiment(experiment_meta)
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    assert services.suggestion_broker.should_ignore(experiment, unprocessed_suggestion, None) is False

  @pytest.mark.parametrize(
    "experiment_type",
    [
      ExperimentMeta.OFFLINE,
      ExperimentMeta.RANDOM,
    ],
  )
  @pytest.mark.parametrize(
    "observation,should_ignore",
    [
      (Observation(data=ObservationData(assignments_map=dict(p1=0))), True),
      (Observation(data=ObservationData(assignments_map=dict(p1=1))), False),
    ],
  )
  def test_same_assignments(
    self,
    services,
    experiment_type,
    observation,
    should_ignore,
    optimization_args,
  ):
    experiment_meta = self.new_experiment_meta(experiment_type=experiment_type)
    experiment = self.new_experiment(experiment_meta)
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    optimization_args = optimization_args.copy_and_set(last_observation=observation)
    assert (
      services.suggestion_broker.should_ignore(experiment, unprocessed_suggestion, optimization_args) is should_ignore
    )
