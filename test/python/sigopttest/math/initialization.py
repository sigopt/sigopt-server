# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.math.initialization import get_low_discrepancy_stencil_length_from_experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *


class TestGetLowDiscrepancyStencilLength:
  @pytest.fixture
  def parameters(self):
    parameters = [ExperimentParameter(param_type=PARAMETER_DOUBLE)] * 10
    parameters.extend(
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
    return parameters

  @pytest.fixture
  def conditional_parameters(self):
    parameters = [
      ExperimentParameter(
        name="d_0",
        param_type=PARAMETER_DOUBLE,
        conditions=[ParameterCondition(name="x", values=[1, 2])],
      ),
    ]
    parameters.extend(
      [
        ExperimentParameter(
          name="d_1",
          param_type=PARAMETER_DOUBLE,
          conditions=[ParameterCondition(name="x", values=[1])],
        ),
      ]
    )
    parameters.extend(
      [
        ExperimentParameter(
          name="c_0",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 3)],
          conditions=[ParameterCondition(name="x", values=[2])],
        ),
        ExperimentParameter(
          name="c_1",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 5)],
          conditions=[ParameterCondition(name="y", values=[3])],
        ),
      ]
    )
    return parameters

  @pytest.fixture
  def conditionals(self):
    conditionals = [
      ExperimentConditional(
        name="x",
        values=[
          ExperimentConditionalValue(name="1", enum_index=1),
          ExperimentConditionalValue(name="2", enum_index=2),
        ],
      ),
      ExperimentConditional(
        name="y",
        values=[
          ExperimentConditionalValue(name="3", enum_index=1),
          ExperimentConditionalValue(name="4", enum_index=2),
          ExperimentConditionalValue(name="5", enum_index=3),
        ],
      ),
    ]
    return conditionals

  def test_no_parameters(self):
    assert get_low_discrepancy_stencil_length_from_experiment(Experiment()) == 4

  def test_no_numeric_parameters(self, parameters):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[p for p in parameters if p.param_type == PARAMETER_CATEGORICAL],
        observation_budget=60,
        development=False,
      ),
    )
    assert get_low_discrepancy_stencil_length_from_experiment(experiment) == 4

  def test_no_categorical_parameters(self, parameters):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[p for p in parameters if not p.param_type == PARAMETER_CATEGORICAL],
        observation_budget=60,
        development=False,
      ),
    )
    assert get_low_discrepancy_stencil_length_from_experiment(experiment) == 10

  def test_max_cap(self, parameters):
    parameters.append(
      ExperimentParameter(
        param_type=PARAMETER_CATEGORICAL,
        all_categorical_values=[ExperimentCategoricalValue(name=str(i), enum_index=i) for i in range(1, 100)],
      )
    )

    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=parameters,
        observation_budget=60,
        development=False,
      ),
    )
    assert get_low_discrepancy_stencil_length_from_experiment(experiment) == 100

  def test_conditional_experiment(self, conditional_parameters, conditionals):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=conditional_parameters,
        conditionals=conditionals,
        observation_budget=60,
        development=False,
      ),
    )
    assert get_low_discrepancy_stencil_length_from_experiment(experiment) == 22

  def test_parallel_experiment(self, parameters):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=parameters,
        observation_budget=60,
        development=False,
        parallel_bandwidth=10,
      ),
    )
    # 10 (numeric parameters) * (4 + 2) (categorical parameters) + (10 - 1) (parallel bandwidth)
    assert get_low_discrepancy_stencil_length_from_experiment(experiment) == 69
