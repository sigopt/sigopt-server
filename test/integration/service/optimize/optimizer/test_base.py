# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation, ObservationDataProxy
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.test_base import ServiceBase
from libsigopt.aux.constant import DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS


class OptimizerServiceTestBase(ServiceBase):
  @pytest.fixture
  def experiment_high_dimension(self, services):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name=f"p{i+1}", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10))
          for i in range(DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS + 1)
        ],
        observation_budget=60,
        development=False,
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def experiment(self, services):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name="p1", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10))
        ],
        observation_budget=60,
        development=False,
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def experiment_categorical(self, services):
    experiment = Experiment(
      client_id=1,
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(
            name="c",
            param_type=PARAMETER_CATEGORICAL,
            all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 3)],
          ),
          ExperimentParameter(name="d", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10)),
          ExperimentParameter(name="i", param_type=PARAMETER_INT, bounds=Bounds(minimum=-10, maximum=10)),
        ],
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def experiment_multimetric(self, services):
    experiment = Experiment(
      client_id=1,
      name="test multimetric experiment",
      experiment_meta=ExperimentMeta(
        metrics=[{"name": "f1"}, {"name": "f2"}],
        all_parameters_unsorted=[
          ExperimentParameter(
            name="p1",
            param_type=PARAMETER_DOUBLE,
            bounds=Bounds(minimum=-10, maximum=10),
          )
        ],
        observation_budget=60,
        development=False,
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def experiment_multisolution(self, services):
    experiment = Experiment(
      client_id=1,
      name="test multisolution experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(
            name="p1",
            param_type=PARAMETER_DOUBLE,
            bounds=Bounds(minimum=-10, maximum=10),
          )
        ],
        observation_budget=60,
        development=False,
        num_solutions=2,
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def experiment_conditionals(self, services):
    experiment = Experiment(
      client_id=1,
      name="test conditionals experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(
            name="p1",
            conditions=[ParameterCondition(name="conditional", values=[1, 2])],
            param_type=PARAMETER_DOUBLE,
            bounds=Bounds(minimum=-10, maximum=10),
          )
        ],
        conditionals=[ExperimentConditional(name="conditional", values=[ExperimentConditionalValue()])],
        observation_budget=60,
        development=False,
      ),
    )
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def parameter(self, experiment):
    return experiment.all_parameters[0]

  def new_unprocessed_suggestion(self, experiment, source=UnprocessedSuggestion.Source.SPE):
    return UnprocessedSuggestion(
      experiment_id=experiment.id,
      source=source,
      suggestion_meta=SuggestionMeta(
        suggestion_data=SuggestionData(
          assignments_map=self.make_assignment_map(experiment),
        ),
      ),
      generated_time=unix_timestamp(),
    )

  @pytest.fixture
  def unprocessed_suggestions(self, experiment):
    return [
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.SPE,
      ),
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.FALLBACK_RANDOM,
      ),
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.LATIN_HYPERCUBE,
      ),
    ]

  def make_assignment_map(self, experiment):
    def get_random_category(param):
      values = param.active_categorical_values
      return random.choice(values).enum_index

    def get_random_bounds(param):
      if param.param_type == PARAMETER_DOUBLE:
        spread = param.bounds.maximum - param.bounds.minimum
        return param.bounds.minimum + random.random() * spread
      return random.randrange(param.bounds.minimum, param.bounds.maximum)

    return {
      p.name: get_random_category(p) if p.param_type == PARAMETER_CATEGORICAL else get_random_bounds(p)
      for p in experiment.all_parameters
    }

  def make_observations(self, services, experiment, num_observations):
    @generator_to_list
    def make_observations_generator(num_observations):
      for _ in range(num_observations):
        observation_data = ObservationData(
          values=[ObservationValue(value=random.random())],
          assignments_map=self.make_assignment_map(experiment),
        )
        yield Observation(data=ObservationDataProxy(observation_data), experiment_id=experiment.id)

    services.observation_service.insert_observations(experiment, make_observations_generator(num_observations))
