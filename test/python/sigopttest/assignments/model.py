# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.assignments.model import HasAssignmentsMap
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentConditional,
  ExperimentParameter,
  ParameterCondition,
)
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData


class TestGetAssignmentsWithConditionals(object):
  @pytest.fixture
  def experiment_no_conditionals(self):
    return Mock(
      conditionals=[],
      all_parameters=[
        ExperimentParameter(
          name="c",
          param_type=PARAMETER_CATEGORICAL,
        ),
        ExperimentParameter(
          name="d",
          param_type=PARAMETER_DOUBLE,
        ),
        ExperimentParameter(
          name="i",
          param_type=PARAMETER_INT,
        ),
      ],
    )

  @pytest.fixture
  def experiment_with_conditionals(self):
    return Mock(
      conditionals=[ExperimentConditional(name="x"), ExperimentConditional(name="y")],
      all_parameters=[
        ExperimentParameter(
          name="c",
          param_type=PARAMETER_CATEGORICAL,
          conditions=[ParameterCondition(name="x", values=[1])],
        ),
        ExperimentParameter(
          name="d",
          param_type=PARAMETER_DOUBLE,
          conditions=[ParameterCondition(name="x", values=[1, 2]), ParameterCondition(name="y", values=[2])],
        ),
        ExperimentParameter(
          name="i",
          param_type=PARAMETER_INT,
        ),
      ],
    )

  def assignments_from_dict(self, assignments_dict):
    # We use our own mock class so it's hard to mock the classname
    return HasAssignmentsMap((ObservationData(assignments_map=assignments_dict)))

  @pytest.mark.parametrize(
    "test,expected",
    [
      (dict(x=1, y=1, c=0, d=0, i=0), dict(x=1, y=1, c=0, i=0)),
      (dict(x=1, y=2, c=0, d=0, i=0), dict(x=1, y=2, c=0, d=0, i=0)),
      (dict(x=2, y=1, c=0, d=0, i=0), dict(x=2, y=1, i=0)),
      (dict(x=2, y=2, c=0, d=0, i=0), dict(x=2, y=2, d=0, i=0)),
      (dict(x=3, y=1, c=0, d=0, i=0), dict(x=3, y=1, i=0)),
      (dict(x=3, y=2, c=0, d=0, i=0), dict(x=3, y=2, i=0)),
    ],
  )
  def test_get_assignments_with_conditionals(self, test, expected, experiment_with_conditionals):
    assignments = self.assignments_from_dict(test)
    assert assignments.get_assignments(experiment_with_conditionals) == expected

  @pytest.mark.parametrize(
    "test",
    [
      (dict(x=1, y=1, c=0, d=0, i=0)),
      (dict(x=1, y=2, c=0, d=0, i=0)),
      (dict(x=2, y=1, c=0, d=0, i=0)),
      (dict(x=2, y=2, c=0, d=0, i=0)),
      (dict(x=3, y=1, c=0, d=0, i=0)),
      (dict(x=3, y=2, c=0, d=0, i=0)),
    ],
  )
  def test_get_assignments_without_conditionals(self, test, experiment_no_conditionals):
    assignments = self.assignments_from_dict(test)
    assert assignments.get_assignments(experiment_no_conditionals) == dict(c=0, i=0, d=0)
