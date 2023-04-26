# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.optimize.args import OptimizationArgs
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta, SuggestionData, SuggestionMeta
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.test_base import ServiceBase


class SuggestionBrokerTestBase(ServiceBase):
  @pytest.fixture
  def optimization_args(self):
    return OptimizationArgs(
      source=None,
      observation_iterator=[],
      observation_count=0,
      failure_count=0,
      max_observation_id=None,
      old_hyperparameters=None,
      open_suggestions=[],
      last_observation=None,
    )

  def populate_db_with_open_suggestions(self, services, experiment, num_open_suggestions):
    for _ in range(num_open_suggestions):
      unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
      services.unprocessed_suggestion_service.process(experiment, unprocessed_suggestion, None)

  def make_observation(self, experiment, assignments, value):
    return Observation(
      data=ObservationData(
        assignments_map=assignments,
        values=[ObservationValue(value=value)],
      ),
      experiment_id=experiment.id,
    )

  def populate_db_with_observations(self, services, experiment, num_observations):
    random_sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    suggestions = random_sampler.generate_random_suggestions(num_observations)
    observations = [
      self.make_observation(
        experiment=experiment,
        assignments=suggestion.suggestion_meta.suggestion_data.get_assignments(experiment),
        value=2 * k,
      )
      for k, suggestion in enumerate(suggestions)
    ]
    services.observation_service.insert_observations(experiment, observations)

  def new_unprocessed_suggestion(self, experiment, p1=0, source=UnprocessedSuggestion.Source.SPE):
    return UnprocessedSuggestion(
      experiment_id=experiment.id,
      source=source,
      suggestion_meta=SuggestionMeta(
        suggestion_data=SuggestionData(
          assignments_map=dict(p1=p1),
        ),
      ),
      generated_time=unix_timestamp(),
    )

  def new_experiment_meta(self, **kwargs):
    create_kwargs = dict(
      all_parameters_unsorted=[
        ExperimentParameter(name="p1", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10))
      ],
      observation_budget=60,
      development=False,
    )
    create_kwargs.update(kwargs)
    return ExperimentMeta(**create_kwargs)  # type: ignore

  def new_experiment(self, experiment_meta=None, parallel_bandwidth=None):
    if experiment_meta is None:
      if parallel_bandwidth is None:
        experiment_meta = self.new_experiment_meta()
      else:
        experiment_meta = self.new_experiment_meta(parallel_bandwidth=parallel_bandwidth)

    return Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=experiment_meta,
    )

  @pytest.fixture
  def experiment(self, services):
    experiment = self.new_experiment()
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def parallel_experiment(self, services):
    experiment = self.new_experiment(parallel_bandwidth=5)
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture(params=[None, "", "{}", '{"foo": "bar"}', "invalid{}json"])
  def processed_suggestion_meta(self, request):
    meta = ProcessedSuggestionMeta()
    if request.param is not None:
      meta.client_provided_data = request.param
    return meta
