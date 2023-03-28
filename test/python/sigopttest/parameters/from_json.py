# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from libsigopt.sigoptaux.constant import ParameterPriorNames
from mock import Mock

from zigopt.net.errors import BadParamError, InvalidKeyError, InvalidTypeError, InvalidValueError
from zigopt.parameters.from_json import (
  set_categorical_values_from_json,
  set_parameter_conditions_from_json,
  set_prior_from_json,
)
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentConditionalValue,
  ExperimentParameter,
)


class TestSetConditionsFromJson(object):
  @pytest.fixture(
    params=[
      PARAMETER_DOUBLE,
      PARAMETER_INT,
      PARAMETER_CATEGORICAL,
    ]
  )
  def parameter(self, request):
    return ExperimentParameter(name="Test Param", param_type=request.param)

  def mock_conditional_values(self, values):
    return [ExperimentConditionalValue(name=v, enum_index=i) for (i, v) in enumerate(values)]

  @pytest.fixture
  def conditionals_map(self):
    return dict(
      x=Mock(name="x", values=self.mock_conditional_values(["1", "5", "10"])),
      y=Mock(name="y", values=self.mock_conditional_values(["a"])),
    )

  @pytest.fixture(
    params=[
      dict(x=["1", "5", "10"], y=["a"]),
      dict(x=["1", "5", "10"], y="a"),
    ]
  )
  def parameter_json(self, request):
    return dict(conditions=request.param)

  def test_set_parameter_conditions_from_json(self, parameter, parameter_json, conditionals_map):
    set_parameter_conditions_from_json(parameter, parameter_json, conditionals_map)

  @pytest.mark.parametrize(
    "empty_parameter_json",
    [
      dict(),
      dict(conditions=None),
      dict(conditions=dict()),
    ],
  )
  def test_no_conditions(self, parameter, empty_parameter_json, conditionals_map):
    set_parameter_conditions_from_json(parameter, empty_parameter_json, conditionals_map)
    assert not parameter.conditions

  @pytest.mark.parametrize(
    "invalid_parameter_json",
    [
      dict(conditions={5: ["1"]}),
      dict(conditions={5: "1"}),
    ],
  )
  def test_invalid_condition_name(self, parameter, invalid_parameter_json, conditionals_map):
    with pytest.raises(InvalidTypeError):
      set_parameter_conditions_from_json(parameter, invalid_parameter_json, conditionals_map)

  @pytest.mark.parametrize(
    "invalid_parameter_json",
    [
      dict(conditions=dict(x=[1, 5, 10])),
      dict(conditions=dict(x=1)),
    ],
  )
  def test_invalid_condition_values(self, parameter, invalid_parameter_json, conditionals_map):
    with pytest.raises(InvalidTypeError):
      set_parameter_conditions_from_json(parameter, invalid_parameter_json, conditionals_map)

  @pytest.mark.parametrize(
    "invalid_parameter_json",
    [
      dict(conditions=dict(x=None)),
      dict(conditions=dict(x=[])),
    ],
  )
  def test_condition_name_with_no_value(self, parameter, invalid_parameter_json, conditionals_map):
    with pytest.raises(BadParamError):
      set_parameter_conditions_from_json(parameter, invalid_parameter_json, conditionals_map)


class TestSetCategoricalValuesFromJson(object):
  @pytest.fixture
  def categorical_parameter(self):
    return ExperimentParameter(
      name="categorical parameter",
      param_type=PARAMETER_CATEGORICAL,
    )

  @pytest.fixture(
    params=[
      dict(categorical_values=[dict(name="a"), dict(name="b")]),
      dict(categorical_values=["a", "b"]),
      dict(categorical_values=[dict(name="a", enum_index=1), dict(name="b", enum_index=2)]),
    ]
  )
  def parameter_json(self, request):
    return request.param

  def assert_expected_parameter(self, parameter):
    (cat1, cat2) = sorted(parameter.all_categorical_values, key=lambda c: c.enum_index)
    assert cat1.enum_index == 1
    assert cat1.name == "a"
    assert cat1.deleted is False
    assert cat2.enum_index == 2
    assert cat2.name == "b"
    assert cat2.deleted is False

  def test_set_categorical_values_from_json(self, categorical_parameter, parameter_json):
    set_categorical_values_from_json(categorical_parameter, parameter_json)
    self.assert_expected_parameter(categorical_parameter)

  def test_invalid_parameter_types(self, parameter_json):
    int_parameter = ExperimentParameter(
      name="int parameter",
      param_type=PARAMETER_INT,
    )
    with pytest.raises(InvalidKeyError):
      set_categorical_values_from_json(int_parameter, parameter_json)

    double_parameter = ExperimentParameter(
      name="double parameter",
      param_type=PARAMETER_DOUBLE,
    )
    with pytest.raises(InvalidKeyError):
      set_categorical_values_from_json(double_parameter, parameter_json)

  @pytest.mark.parametrize(
    "invalid_parameter_json",
    [
      dict(),
      dict(categorical_values=[]),
      dict(categorical_values=["a"]),
      dict(categorical_values=[dict(name="a")]),
      dict(categorical_values=[dict(name="a", enum_index=1)]),
    ],
  )
  def test_too_few_categorical_values(self, categorical_parameter, invalid_parameter_json):
    with pytest.raises(BadParamError):
      set_categorical_values_from_json(categorical_parameter, invalid_parameter_json)

  @pytest.mark.parametrize(
    "invalid_parameter_json",
    [
      dict(categorical_values=["a", "a"]),
      dict(categorical_values=[dict(name="a"), dict(name="a")]),
      dict(categorical_values=[dict(name="a", enum_index=1), dict(name="a", enum_index=2)]),
    ],
  )
  def test_duplicate_names(self, categorical_parameter, invalid_parameter_json):
    with pytest.raises(InvalidValueError):
      set_categorical_values_from_json(categorical_parameter, invalid_parameter_json)

  @pytest.mark.parametrize(
    "mixed_parameter_json",
    [
      dict(categorical_values=["a", dict(name="b")]),
      dict(categorical_values=[dict(name="a"), dict(name="b", enum_index=2)]),
      dict(categorical_values=[dict(name="a", enum_index=1), "b"]),
    ],
  )
  def test_mixed_categorical_values_array(self, categorical_parameter, mixed_parameter_json):
    set_categorical_values_from_json(categorical_parameter, mixed_parameter_json)
    self.assert_expected_parameter(categorical_parameter)


class TestSetPriorFromJson(object):
  @pytest.fixture
  def double_parameter(self):
    return ExperimentParameter(
      name="double parameter",
      param_type=PARAMETER_DOUBLE,
    )

  def test_invalid_parameter_types(self):
    parameter_json = dict(prior=dict(name=ParameterPriorNames.NORMAL, mean=0, scale=1))

    int_parameter = ExperimentParameter(
      name="int parameter",
      param_type=PARAMETER_INT,
    )
    with pytest.raises(InvalidKeyError):
      set_prior_from_json(int_parameter, parameter_json)

    categorical_parameter = ExperimentParameter(
      name="categorical parameter",
      param_type=PARAMETER_CATEGORICAL,
    )
    with pytest.raises(InvalidKeyError):
      set_prior_from_json(categorical_parameter, parameter_json)

  def test_undefined_prior_types(self, double_parameter):
    parameter_json = dict(prior=dict(name="undefined_prior"))
    with pytest.raises(InvalidValueError):
      set_prior_from_json(double_parameter, parameter_json)

  def test_set_normal_prior_from_json(self, double_parameter):
    parameter_json = dict(prior=dict(name=ParameterPriorNames.NORMAL, mean=0, scale=1))
    set_prior_from_json(double_parameter, parameter_json)
    assert double_parameter.prior.normal_prior.mean == 0
    assert double_parameter.prior.normal_prior.scale == 1

    parameter_json = dict(prior=dict(name=ParameterPriorNames.NORMAL, mean=0, scale=-1))
    with pytest.raises(BadParamError):
      set_prior_from_json(double_parameter, parameter_json)

  def test_set_beta_prior_from_json(self, double_parameter):
    parameter_json = dict(prior=dict(name=ParameterPriorNames.BETA, shape_a=1, shape_b=2))
    set_prior_from_json(double_parameter, parameter_json)
    assert double_parameter.prior.beta_prior.shape_a == 1
    assert double_parameter.prior.beta_prior.shape_b == 2

    parameter_json = dict(prior=dict(name=ParameterPriorNames.BETA, shape_a=0, shape_b=2))
    with pytest.raises(BadParamError):
      set_prior_from_json(double_parameter, parameter_json)
