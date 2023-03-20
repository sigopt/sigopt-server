# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.optimize.sources.conditional import ConditionalOptimizationSource
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.sigoptcompute.adapter import SCAdapter
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from sigopttest.base.utils import partial_opt_args
from sigopttest.optimize.sources.base_test import UnitTestBase


class TestExperimentProgress(object):
  def test_hyper_opt_dimension(self):
    json_dict = dict(
      name="conditional-hp-test",
      parameters=[
        dict(name="a", type="int", bounds=dict(min=1, max=50)),
        dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(x=["5", "10"])),
        dict(
          name="c",
          type="categorical",
          categorical_values=[dict(name="d"), dict(name="e")],
          conditions=dict(x="1"),
        ),
      ],
      conditionals=[dict(name="x", values=["1", "5", "10"])],
    )
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = ConditionalOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 2 + 2 + 3

    json_dict = dict(
      name="conditional-hp-test",
      parameters=[
        dict(name="a", type="int", bounds=dict(min=1, max=50), conditions=dict(y="v")),
        dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(x=["5", "10"])),
        dict(name="c", type="int", bounds=dict(min=20, max=750), conditions=dict(x="1")),
        dict(name="d", type="double", bounds=dict(min=-10, max=10), conditions=dict(y=["u", "w"])),
      ],
      conditionals=[dict(name="x", values=["1", "5", "10"]), dict(name="y", values=["u", "v", "w"])],
    )
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = ConditionalOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 4 + 3 * 2


class TestSourceFunctionality(UnitTestBase):
  @pytest.fixture
  def experiment(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
          conditions=[ParameterCondition(name="cond", values=[1])],
        ),
        ExperimentParameter(
          name="integer",
          param_type=PARAMETER_INT,
          bounds=Bounds(minimum=-14, maximum=12),
          conditions=[ParameterCondition(name="cond", values=[2])],
        ),
        ExperimentParameter(
          name="categorical",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0_0", enum_index=0),
            ExperimentCategoricalValue(name="c0_1", enum_index=1),
          ],
          conditions=[ParameterCondition(name="cond", values=[3])],
        ),
      ],
      conditionals=[
        ExperimentConditional(
          name="cond",
          values=[
            ExperimentConditionalValue(name="activate_double", enum_index=1),
            ExperimentConditionalValue(name="activate_integer", enum_index=2),
            ExperimentConditionalValue(name="activate_categorical", enum_index=3),
          ],
        )
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

  @pytest.mark.parametrize("max_gp_observations", (5, 7, 8))
  def test_suggestions_in_conditional_assignments(self, services, experiment, max_gp_observations):
    services.config_broker["model.max_simultaneous_af_points"] = 10
    services.config_broker["model.nonzero_mean_default"] = "automatic"
    services.config_broker["model.num_suggestions"] = 1
    services.config_broker["model.gp_cutoff_observation_count"] = max_gp_observations

    num_suggestions = 7
    source = ConditionalOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, num_suggestions)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    services.sc_adapter = SCAdapter(services)
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    unprocessed = source.get_suggestions(optimization_args)
    for u in unprocessed:
      assert u.experiment_id == experiment.id
      if num_suggestions < max_gp_observations:
        assert u.source == UnprocessedSuggestion.Source.GP_CATEGORICAL
      else:
        assert u.source == UnprocessedSuggestion.Source.EXPLICIT_RANDOM
      has_assignments = u.suggestion_meta.suggestion_data.copy_protobuf()
      values_dict = has_assignments.assignments_map
      assert len(values_dict) == 2
      conditional_assignment = u.suggestion_meta.get_conditional_assignments(experiment)
      assert conditional_assignment and "cond" in conditional_assignment
      assert conditional_assignment["cond"] in (1.0, 2.0, 3.0)
      if conditional_assignment["cond"] == 1.0:
        assert "integer" not in values_dict and "categorical" not in values_dict
        assert "double" in values_dict
      elif conditional_assignment["cond"] == 2.0:
        assert "double" not in values_dict and "categorical" not in values_dict
        assert "integer" in values_dict
      else:
        assert "double" not in values_dict and "integer" not in values_dict
        assert "categorical" in values_dict

  def test_hyperparameter_length(self, services, experiment):
    source = ConditionalOptimizationSource(services, experiment)
    suggestions = self.sample_suggestions(services, experiment, 7)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    services.sc_adapter = SCAdapter(services)
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    hp = source.get_hyperparameters(optimization_args)
    all_lengthscales = hp.multimetric_hyperparameter_value[0].categorical_hyperparameters.hyperparameter_lengths
    assert len(all_lengthscales) == 4
    hp_names = [ls.parameter_name for ls in all_lengthscales]
    assert set(hp_names) == set(("cond", "double", "integer", "categorical"))
