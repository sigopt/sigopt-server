# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.suggestion.sampler.base import SequentialSampler
from zigopt.suggestion.sampler.categorical import CategoricalOnlySampler
from zigopt.suggestion.sampler.grid import GridSampler
from zigopt.suggestion.sampler.queue import SuggestionQueueSampler
from zigopt.suggestion.sampler.random import RandomSampler

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase
from sigopttest.base.utils import partial_opt_args


class TestNextSampler(SuggestionBrokerTestBase):
  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize(
    "experiment_type",
    [
      ExperimentMeta.OFFLINE,
      ExperimentMeta.RANDOM,
      ExperimentMeta.GRID,
    ],
  )
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_development(self, services, num_observations, experiment_type, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.development = True
    experiment_meta.experiment_type = experiment_type
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler, RandomSampler) is True

  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_random(self, services, num_observations, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.experiment_type = ExperimentMeta.RANDOM
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler, RandomSampler) is True

  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_grid(self, services, num_observations, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.experiment_type = ExperimentMeta.GRID
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler, GridSampler) is True

  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_only_categorical_parameters(self, services, num_observations, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.all_parameters_unsorted.clear()
    experiment_meta.all_parameters_unsorted.extend(
      [
        ExperimentParameter(
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 3)],
        ),
        ExperimentParameter(
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 5)],
        ),
      ]
    )
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler, CategoricalOnlySampler) is True

  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_other_types_use_sequential_sampler(self, services, num_observations, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.experiment_type = ExperimentMeta.OFFLINE
    experiment = self.new_experiment(experiment_meta)
    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler, SequentialSampler)

  @pytest.mark.parametrize("num_observations", [0, 100, 600])
  @pytest.mark.parametrize(
    "experiment_type,expected_sampler",
    [
      (ExperimentMeta.OFFLINE, SuggestionQueueSampler),
    ],
  )
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_last_sequential_sampler(
    self, services, num_observations, experiment_type, expected_sampler, num_open_suggestions
  ):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.experiment_type = experiment_type
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert isinstance(sampler.samplers_with_counts[-1][0], expected_sampler)

  @pytest.mark.parametrize(
    "num_observations,expected_num_samplers",
    [
      (0, 2),
      (1, 2),
      (2, 2),
      (3, 2),
      (4, 1),
      (100, 1),
      (600, 1),
    ],
  )
  @pytest.mark.parametrize("num_open_suggestions", [0, 1])
  def test_first_sequential_sampler(self, services, num_observations, expected_num_samplers, num_open_suggestions):
    experiment_meta = self.new_experiment_meta()
    experiment_meta.experiment_type = ExperimentMeta.OFFLINE
    experiment = self.new_experiment(experiment_meta)

    open_suggestions = num_open_suggestions * [Mock()]
    optimization_args = partial_opt_args(observation_count=num_observations, open_suggestions=open_suggestions)
    sampler = services.suggestion_broker.next_sampler(experiment, optimization_args)
    assert len(sampler.samplers_with_counts) == expected_num_samplers
