# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.conditionals.util import convert_to_unconditioned_experiment
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *


class TestConvertToUnconditionedExperiment:
  @pytest.fixture
  def experiment(self):
    return Experiment(
      experiment_meta=ExperimentMeta(
        conditionals=[ExperimentConditional(name="x"), ExperimentConditional(name="y")],
        all_parameters_unsorted=[
          ExperimentParameter(
            name="c",
            param_type=PARAMETER_CATEGORICAL,
            all_categorical_values=[
              ExperimentCategoricalValue(name="c1", enum_index=1),
              ExperimentCategoricalValue(name="c2", enum_index=2),
            ],
            conditions=[ParameterCondition(name="x", values=[1])],
          ),
          ExperimentParameter(
            name="d",
            param_type=PARAMETER_DOUBLE,
            bounds=Bounds(minimum=0, maximum=1),
            conditions=[ParameterCondition(name="x", values=[1, 2]), ParameterCondition(name="y", values=[2])],
          ),
          ExperimentParameter(
            name="i",
            param_type=PARAMETER_INT,
            bounds=Bounds(minimum=5, maximum=15),
          ),
        ],
      )
    )

  def test_convert_to_unconditioned_experiment(self, experiment):
    expected_parameter_names = ["c", "d", "i", "x", "y"]
    unconditioned_experiment = convert_to_unconditioned_experiment(experiment)
    parameters = unconditioned_experiment.experiment_meta.all_parameters_unsorted
    param_names = [param.name for param in parameters]
    assert set(param_names) == set(expected_parameter_names)
    assert all(p.param_type == PARAMETER_CATEGORICAL for p in parameters if p.name in ("x", "y"))
