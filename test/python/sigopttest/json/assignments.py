# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment, ExperimentMetaProxy
from zigopt.json.assignments import assignments_json, render_conditional_value
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentConditional,
  ExperimentConditionalValue,
  ExperimentMeta,
  ExperimentParameter,
  ParameterCondition,
)


class _TestAssignmentsJsonBase:
  @pytest.fixture
  def categorical_param(self):
    p = ExperimentParameter(
      name="categorical_param",
      param_type=PARAMETER_CATEGORICAL,
    )
    for idx, name in enumerate(["a", "b", "c"], start=1):
      c = p.all_categorical_values.add()
      c.enum_index = idx
      c.name = name
    return p

  @pytest.fixture
  def deleted_param(self):
    return ExperimentParameter(
      name="deleted_param",
      deleted=True,
      param_type=PARAMETER_INT,
    )

  @pytest.fixture
  def double_param(self):
    return ExperimentParameter(
      name="double_param",
      param_type=PARAMETER_DOUBLE,
    )

  @pytest.fixture
  def int_param(self):
    return ExperimentParameter(
      name="int_param",
      param_type=PARAMETER_INT,
    )

  @pytest.fixture
  def parameters(
    self,
    categorical_param,
    deleted_param,
    double_param,
    int_param,
  ):
    return [
      categorical_param,
      deleted_param,
      double_param,
      int_param,
    ]


class TestAssignmentsJson(_TestAssignmentsJsonBase):
  @pytest.fixture
  def experiment(
    self,
    categorical_param,
    deleted_param,
    double_param,
    int_param,
  ):
    meta = ExperimentMeta(
      all_parameters_unsorted=[
        categorical_param,
        deleted_param,
        double_param,
        int_param,
      ],
    )
    return Experiment(experiment_meta=ExperimentMetaProxy(meta))

  def test_assignments_json(self, experiment):
    assert assignments_json(experiment, dict(categorical_param=1, double_param=2.4, int_param=3.2,)) == dict(
      categorical_param="a",
      double_param=2.4,
      int_param=3,
    )

  def test_includes_deleted_parameters(self, experiment):
    assert assignments_json(
      experiment,
      dict(
        categorical_param=1,
        deleted_param=5.7,
        double_param=2.4,
        int_param=3.2,
      ),
    ) == dict(
      categorical_param="a",
      deleted_param=5,
      double_param=2.4,
      int_param=3,
    )

  def test_no_error_on_missing_values(self, experiment):
    assert assignments_json(experiment, dict()) == dict()

  def test_unknown_parameter(self, experiment):
    with pytest.raises(Exception):
      assignments_json(
        experiment,
        dict(
          categorical_param=1,
          double_param=2.4,
          int_param=3.2,
          unknown_param=6.7,
        ),
      )


class TestAssignmentsJsonWithConditionals(_TestAssignmentsJsonBase):
  @pytest.fixture
  def conditional(self):
    return ExperimentConditional(
      name="x",
      values=[
        ExperimentConditionalValue(name="2", enum_index=1),
        ExperimentConditionalValue(name="4", enum_index=2),
        ExperimentConditionalValue(name="6", enum_index=3),
      ],
    )

  @pytest.fixture
  def experiment(
    self,
    categorical_param,
    conditional,
    deleted_param,
    double_param,
    int_param,
  ):
    int_param.conditions.extend([ParameterCondition(name="x", values=[1, 2])])
    double_param.conditions.extend([ParameterCondition(name="x", values=[1])])
    meta = ExperimentMeta(
      all_parameters_unsorted=[
        categorical_param,
        deleted_param,
        double_param,
        int_param,
      ],
      conditionals=[
        conditional,
      ],
    )
    return Experiment(experiment_meta=ExperimentMetaProxy(meta))

  def test_without_conditionals(self, experiment):
    assert assignments_json(experiment, dict(categorical_param=1, double_param=2.4, int_param=3.2,)) == dict(
      categorical_param="a",
      double_param=2.4,
      int_param=3,
    )

  def test_with_conditionals(self, experiment):
    assert assignments_json(experiment, dict(categorical_param=1, double_param=2.4, int_param=3.2, x=1,)) == dict(
      categorical_param="a",
      double_param=2.4,
      int_param=3,
      x="2",
    )

  def test_with_unsatisfied_parameters(self, experiment):
    assert assignments_json(experiment, dict(categorical_param=1, double_param=2.4, int_param=3.2, x=2,)) == dict(
      categorical_param="a",
      double_param=None,
      int_param=3,
      x="4",
    )

    assert assignments_json(experiment, dict(categorical_param=1, double_param=2.4, int_param=3.2, x=3,)) == dict(
      categorical_param="a",
      double_param=None,
      int_param=None,
      x="6",
    )

  def test_includes_deleted_parameters(self, experiment):
    assert assignments_json(
      experiment,
      dict(
        categorical_param=1,
        deleted_param=5.7,
        double_param=2.4,
        int_param=3.2,
        x=1,
      ),
    ) == dict(
      categorical_param="a",
      deleted_param=5,
      double_param=2.4,
      int_param=3,
      x="2",
    )

  def test_no_error_on_missing_values(self, experiment):
    assert assignments_json(experiment, dict()) == dict()

  def test_unknown_parameter(self, experiment):
    with pytest.raises(Exception):
      assignments_json(
        experiment,
        dict(
          categorical_param=1,
          double_param=2.4,
          int_param=3.2,
          unknown_param=6.7,
          x="2",
        ),
      )


class TestRenderConditionalValue:
  @pytest.fixture
  def conditional(self):
    conditional = ExperimentConditional(
      name="x",
      values=[
        ExperimentConditionalValue(name="2", enum_index=1),
        ExperimentConditionalValue(name="4", enum_index=2),
        ExperimentConditionalValue(name="6", enum_index=3),
      ],
    )
    return conditional

  @pytest.mark.parametrize(
    "assignment,expected",
    [
      (1, "2"),
      (2, "4"),
      (3, "6"),
    ],
  )
  def test_render_conditional_value(self, conditional, assignment, expected):
    assert render_conditional_value(conditional, assignment) == expected

  @pytest.mark.parametrize(
    "assignment",
    [
      None,
      0,
      4,
      "2",
      "4",
      "6",
    ],
  )
  def test_invalid_values(self, conditional, assignment):
    with pytest.raises(Exception):
      render_conditional_value(conditional, assignment)
