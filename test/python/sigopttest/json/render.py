# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import ExperimentParameterProxy
from zigopt.json.render import render_param_value
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentParameter,
)


class _TestParameterJsonBase:
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
    return ExperimentParameterProxy(p)

  @pytest.fixture
  def deleted_param(self):
    p = ExperimentParameter(
      name="deleted_param",
      deleted=True,
      param_type=PARAMETER_INT,
    )
    return ExperimentParameterProxy(p)

  @pytest.fixture
  def double_param(self):
    p = ExperimentParameter(
      name="double_param",
      param_type=PARAMETER_DOUBLE,
    )
    return ExperimentParameterProxy(p)

  @pytest.fixture
  def int_param(self):
    p = ExperimentParameter(
      name="int_param",
      param_type=PARAMETER_INT,
    )
    return ExperimentParameterProxy(p)


class TestRenderParamValue(_TestParameterJsonBase):
  @pytest.mark.parametrize(
    "assignment,expected",
    [
      (1, "a"),
      (2, "b"),
      (3, "c"),
    ],
  )
  def test_render_categorical_param_value(self, categorical_param, assignment, expected):
    assert render_param_value(categorical_param, assignment) == expected

  @pytest.mark.parametrize(
    "assignment,expected",
    [
      (1, 1),
      (2.2, 2),
      (-1.2, -1),
      (-2, -2),
    ],
  )
  def test_render_deleted_param_value(self, deleted_param, assignment, expected):
    assert render_param_value(deleted_param, assignment) == expected

  @pytest.mark.parametrize(
    "assignment,expected",
    [
      (1, 1),
      (2.2, 2),
      (-1.2, -1),
      (-2, -2),
    ],
  )
  def test_render_int_param_value(self, int_param, assignment, expected):
    assert render_param_value(int_param, assignment) == expected

  @pytest.mark.parametrize(
    "assignment",
    [
      -1,
      2.2,
      -1.2,
      -2,
    ],
  )
  def test_render_double_param_value(self, double_param, assignment):
    assert render_param_value(double_param, assignment) == assignment

  @pytest.mark.parametrize(
    "assignment",
    [
      0,
      4,
      None,
    ],
  )
  def test_unknown_categorical_assignment(self, categorical_param, assignment):
    with pytest.raises(Exception):
      render_param_value(categorical_param, assignment)

  def test_param_is_none(self):
    with pytest.raises(Exception):
      render_param_value(None, 1)  # type: ignore
