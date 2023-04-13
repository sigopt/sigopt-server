# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random
from collections import defaultdict

import mock
import pytest
from sigopt_config.broker import ConfigBroker

from zigopt.assignments.model import make_experiment_assignment_value_array
from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.optimize.sources.base import OptimizationSource
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.optimize.sources.search import SearchOptimizationSource
from zigopt.optimize.sources.spe import SPEOptimizationSource
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.sigoptcompute.adapter import SCAdapter
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from sigopttest.base.utils import partial_opt_args


class UnitTestBase:
  @pytest.fixture
  def services(self):
    return mock.Mock(
      config_broker=ConfigBroker({}),
      sc_adapter=SCAdapter(mock.Mock()),
    )

  @pytest.fixture
  def experiment(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(name="x0", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-1, maximum=1)),
        ExperimentParameter(name="i0", param_type=PARAMETER_INT, bounds=Bounds(minimum=-14, maximum=12)),
        ExperimentParameter(
          name="c0",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0_0", enum_index=0),
            ExperimentCategoricalValue(name="c0_1", enum_index=1),
          ],
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      metrics=[
        ExperimentMetric(name="m0"),
      ],
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="sample experiment",
    )

  @staticmethod
  def sample_suggestions(services, experiment, count):
    random_sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    suggestions = []
    for _ in range(count):
      suggestion, _ = random_sampler.best_suggestion()
      suggestion.generated_time = random.random()
      suggestions.append(suggestion)
    return suggestions

  @staticmethod
  def form_random_observations_from_suggestions(experiment, suggestions, observation_values=None):
    return [
      Observation(
        data=ObservationData(
          assignments_map=s.suggestion_meta.get_assignments(experiment),
          values=[
            ObservationValue(
              name=f"m{metric}",
              value=random.random() if observation_values is None else observation_values[i],
              value_var=1e-4,
            )
            for metric in range(len(experiment.all_metrics))
          ],
        ),
        id=i,
      )
      for i, s in enumerate(suggestions)
    ]

  def create_experiment(self, feature=""):
    features = defaultdict(bool)
    features[feature] = True

    if features["constraints"]:
      constraints_list = [
        ExperimentConstraint(
          type="less_than",
          terms=[
            Term(name="x0", coeff=1),
          ],
          rhs=1,
        ),
      ]
    else:
      constraints_list = []
    if features["conditionals"]:
      conditionals = [
        ExperimentConditional(),
        ExperimentConditional(),
      ]
    else:
      conditionals = []
    if features["multimetric"]:
      metrics = [ExperimentMetric(name="m0"), ExperimentMetric(name="m1")]
    else:
      metrics = [ExperimentMetric(name="m0")]
    num_solutions = 2 if features["multisolution"] else 1
    parallel_bandwidth = 2

    parameters = [
      ExperimentParameter(name="x0", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-1, maximum=1)),
      ExperimentParameter(name="i0", param_type=PARAMETER_INT, bounds=Bounds(minimum=-14, maximum=12)),
      ExperimentParameter(
        name="c0",
        param_type=PARAMETER_CATEGORICAL,
        all_categorical_values=[
          ExperimentCategoricalValue(name="c0_0", enum_index=0),
          ExperimentCategoricalValue(name="c0_1", enum_index=1),
        ],
      ),
    ]
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=parameters,
      observation_budget=100,
      parallel_bandwidth=parallel_bandwidth,
      constraints=constraints_list,
      conditionals=conditionals,
      num_solutions=num_solutions,
      metrics=metrics,
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="test experiment",
    )


class TestSourceFunctionality(UnitTestBase):
  def test_spe_does_not_rerank_random_padding(self, services, experiment):
    source = SPEOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, 10)
    random_padding_suggestions = self.sample_suggestions(services, experiment, 5)
    scored_suggestions = source.get_scored_suggestions(suggestions, None, random_padding_suggestions)
    assert len(scored_suggestions) == 10
    for scored_suggestion in scored_suggestions:
      assert scored_suggestion.suggestion in suggestions

  def test_categorical_scoring(self, services, experiment):
    model = services.config_broker.data.setdefault("model", {})
    model["max_simultaneous_af_points"] = 1000
    model["nonzero_mean_default"] = "automatic"
    source = CategoricalOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, 10)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)

    # Confirm new suggestions would get reasonable EI values
    services.sc_adapter = SCAdapter(services)
    new_suggestions = self.sample_suggestions(services, experiment, 20)
    random_padding_suggestions = self.sample_suggestions(services, experiment, 10)
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    scored_new_suggestions = source.get_scored_suggestions(
      new_suggestions,
      optimization_args,
      random_padding_suggestions,
    )
    assert all(s.score >= 0.0 for s in scored_new_suggestions)

    # Confirm suggestions at existing data points get lower values
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    scored_old_suggestions = source.get_scored_suggestions(suggestions, optimization_args, [])
    best_new_suggestion = max(scored_new_suggestions, key=lambda x: x.score)
    assert all(os.score <= best_new_suggestion.score for os in scored_old_suggestions)

  # TODO(RTL-130): implement a reranking strategy for search very soon
  def test_search_does_not_rerank_random_padding(self, services, experiment):
    source = SearchOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, 10)
    random_padding_suggestions = self.sample_suggestions(services, experiment, 5)
    scored_suggestions = source.get_scored_suggestions(suggestions, None, random_padding_suggestions)
    assert len(scored_suggestions) == 10
    for scored_suggestion in scored_suggestions:
      assert scored_suggestion.suggestion in suggestions

  def test_unprocessed_creation(self, services, experiment):
    source = OptimizationSource(services, experiment)
    source_number = 0
    suggestions = self.sample_suggestions(services, experiment, 10)
    suggestion_data_proxies = [s.suggestion_meta.suggestion_data for s in suggestions]
    unprocessed = source.create_unprocessed_suggestions(suggestion_data_proxies, source_number)
    p = experiment.all_parameters
    for u, s in zip(unprocessed, suggestions):
      assert u.experiment_id == experiment.id
      assert u.source == source_number
      unprocessed_array = make_experiment_assignment_value_array(u.suggestion_meta.suggestion_data, p)
      original_array = make_experiment_assignment_value_array(s.suggestion_meta.suggestion_data, p)
      assert sum(unprocessed_array - original_array) == 0


class TestSourcesGetSuggestionsLogScale(UnitTestBase):
  @pytest.fixture
  def experiment(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
        ),
        ExperimentParameter(
          name="double_log",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=1e-5, maximum=1),
          transformation=ExperimentParameter.TRANSFORMATION_LOG,
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      metrics=[
        ExperimentMetric(name="m0"),
      ],
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="log parameter experiment",
    )

  def test_categorical_suggestions_with_parameter_log_transform(self, services, experiment):
    services.config_broker["model.max_simultaneous_af_points"] = 10
    services.config_broker["model.nonzero_mean_default"] = "automatic"
    services.config_broker["model.num_suggestions"] = 1

    source = CategoricalOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, 7)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    services.sc_adapter = SCAdapter(services)
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    unprocessed = source.get_suggestions(optimization_args)
    for u in unprocessed:
      assert u.experiment_id == experiment.id
      assert u.source == UnprocessedSuggestion.Source.GP_CATEGORICAL
      has_assignments = u.suggestion_meta.suggestion_data.copy_protobuf()
      values_dict = has_assignments.assignments_map
      assert len(values_dict) == 2
      assert "double" in values_dict
      assert -1 <= values_dict["double"] <= 1
      assert "double_log" in values_dict
      assert 1e-5 <= values_dict["double_log"] <= 1

  @pytest.mark.parametrize("num_observations", [3, 20, 50, 90])
  def test_spe_suggestions_with_parameter_log_transform(self, services, experiment, num_observations):
    services.config_broker["model.num_suggestions"] = 2

    source = SPEOptimizationSource(services, experiment)
    services.sc_adapter = SCAdapter(services)
    suggestions = self.sample_suggestions(services, experiment, num_observations)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    unprocessed = source.get_suggestions(optimization_args)
    for u in unprocessed:
      assert u.experiment_id == experiment.id
      assert u.source == UnprocessedSuggestion.Source.SPE
      has_assignments = u.suggestion_meta.suggestion_data.copy_protobuf()
      values_dict = has_assignments.assignments_map
      assert len(values_dict) == 2
      assert "double" in values_dict
      assert -1 <= values_dict["double"] <= 1
      assert "double_log" in values_dict
      assert 1e-5 <= values_dict["double_log"] <= 1
