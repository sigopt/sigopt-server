# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta, SuggestionData, SuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.test_base import ServiceBase


class UnprocessedSuggestionServiceTestBase(ServiceBase):
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

  def new_conditional_unprocessed_suggestion(self, experiment, p1=0, c1=1, source=UnprocessedSuggestion.Source.SPE):
    return UnprocessedSuggestion(
      experiment_id=experiment.id,
      source=source,
      suggestion_meta=SuggestionMeta(
        suggestion_data=SuggestionData(
          assignments_map=dict(p1=p1, c1=c1),
        ),
      ),
      generated_time=unix_timestamp(),
    )

  def new_experiment(self):
    return Experiment(
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

  def new_conditional_experiment(self):
    return Experiment(
      client_id=1,
      name="test conditional experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name="p1", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10))
        ],
        conditionals=[ExperimentConditional(name="c1", values=[ExperimentConditionalValue(name="cv1", enum_index=1)])],
        observation_budget=60,
        development=False,
      ),
    )

  @pytest.fixture
  def experiment(self, services):
    experiment = self.new_experiment()
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def conditional_experiment(self, services):
    experiment = self.new_conditional_experiment()
    services.experiment_service.insert(experiment)
    return experiment

  @pytest.fixture
  def parameter(self, experiment):
    return experiment.all_parameters[0]

  @pytest.fixture(params=[True, False])
  def include_deleted(self, request):
    return request.param

  @pytest.fixture(params=[True, False])
  def unprocessed_suggestions(self, request, services, experiment):
    unprocessed_suggestions = [
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.SPE,
        p1=0,
      ),
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.FALLBACK_RANDOM,
        p1=-10,
      ),
      self.new_unprocessed_suggestion(
        experiment,
        source=UnprocessedSuggestion.Source.LATIN_HYPERCUBE,
        p1=10,
      ),
    ]
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed(unprocessed_suggestions)
    if request.param:
      for unprocessed_suggestion in unprocessed_suggestions:
        services.unprocessed_suggestion_service.process(
          experiment=experiment,
          unprocessed_suggestion=unprocessed_suggestion,
          processed_suggestion_meta=ProcessedSuggestionMeta(),
        )
    return unprocessed_suggestions

  @pytest.fixture
  def unprocessed_suggestion(self, services, experiment):
    unprocessed_suggestion = self.new_unprocessed_suggestion(experiment)
    services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed_suggestion])
    return unprocessed_suggestion
