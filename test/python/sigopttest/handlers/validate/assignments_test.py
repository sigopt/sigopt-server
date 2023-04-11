# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.experiment.model import Experiment
from zigopt.handlers.validate.assignments import parameter_conditions_satisfied, validate_assignments_map
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta, ParameterCondition


class TestParameterConditionsSatisfied:
  @pytest.fixture(
    params=[
      None,
      [],
    ]
  )
  def param_empty_conditions(self, request):
    return Mock(conditions=request.param)

  @pytest.fixture
  def param_with_conditions(self):
    return Mock(
      conditions=[
        ParameterCondition(name="x", values=[1, 2]),
        ParameterCondition(name="y", values=[1]),
      ]
    )

  @pytest.mark.parametrize(
    "json_dict",
    [
      None,
      dict(),
      dict(x=3),
      dict(y=2),
    ],
  )
  def test_empty_conditions_always_satisfied(self, param_empty_conditions, json_dict):
    assert parameter_conditions_satisfied(param_empty_conditions, json_dict) is True

  @pytest.mark.parametrize(
    "json_dict",
    [
      dict(x=3),
      dict(y=2),
      dict(x=2, y=2),
      dict(x=3, y=1),
    ],
  )
  def test_not_satisfied(self, param_with_conditions, json_dict):
    assert parameter_conditions_satisfied(param_with_conditions, json_dict) is False

  @pytest.mark.parametrize("x", [1, 2])
  @pytest.mark.parametrize("y", [1])
  def test_satisfied(self, param_with_conditions, x, y):
    assert parameter_conditions_satisfied(param_with_conditions, dict(x=x, y=y)) is True

  @pytest.mark.parametrize("x", [1, 2])
  @pytest.mark.parametrize("y", [1])
  @pytest.mark.parametrize("z", [1])
  def test_extra_param(self, param_with_conditions, x, y, z):
    assert parameter_conditions_satisfied(param_with_conditions, dict(x=x, y=y, z=z)) is True

  @pytest.mark.parametrize("x", [1, 2])
  def test_missing_param(self, param_with_conditions, x):
    assert parameter_conditions_satisfied(param_with_conditions, dict(x=x)) is True

  def test_missing_empty(self, param_with_conditions):
    assert parameter_conditions_satisfied(param_with_conditions, dict()) is True

  @pytest.mark.parametrize(
    "parameter",
    [
      param_with_conditions,
      param_empty_conditions,
    ],
  )
  def test_json_dict_is_None(self, parameter):
    with pytest.raises(Exception):
      parameter_conditions_satisfied(parameter, None)


# Note: Mocking the 'name' attribute does not work as expected
# See https://bradmontgomery.net/blog/how-world-do-you-mock-name-attribute/
class TestValidateAssingmentsMap:
  @pytest.fixture
  def experiment(self):
    meta = ExperimentMeta()
    meta.all_parameters_unsorted.add(name="a")
    meta.all_parameters_unsorted.add(name="b")
    meta.all_parameters_unsorted.add(name="c")

    return Experiment(experiment_meta=meta)

  @pytest.fixture
  def experiment_with_conditionals(self):
    meta = ExperimentMeta()
    p = meta.all_parameters_unsorted.add(name="a")
    p = meta.all_parameters_unsorted.add(name="b")
    p.conditions.add(name="c", values=[1])
    meta.conditionals.add(name="c")

    return Experiment(experiment_meta=meta)

  @pytest.fixture(params=["conditionals", "default"])
  def any_experiment(self, request, experiment, experiment_with_conditionals):
    if request.param == "default":
      return experiment
    if request.param == "conditionals":
      return experiment_with_conditionals
    return None

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=0, b=0, c=1),
      dict(a=-1, b=0.5, c=1),
    ],
  )
  def test_valid_assignments_map(self, any_experiment, assignments):
    validate_assignments_map(assignments, any_experiment)

  def test_ignore_extra_assignment(self, any_experiment):
    validate_assignments_map(dict(a=0, b=0, c=1, d=0), any_experiment)

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(c=1, a=0),
      dict(c=1, b=0.5),
      dict(),
    ],
  )
  def test_missing_parameters(self, experiment, assignments):
    with pytest.raises(BadParamError):
      validate_assignments_map(assignments, experiment)

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(c=2, a=0),
      dict(c=3, a=-1),
    ],
  )
  def test_missing_unsatisfied_parameters(self, experiment_with_conditionals, assignments):
    validate_assignments_map(assignments, experiment_with_conditionals)

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(c=1, b=0),
      dict(c=2),
    ],
  )
  def test_missing_satisfied_parameters(self, experiment_with_conditionals, assignments):
    with pytest.raises(BadParamError):
      validate_assignments_map(assignments, experiment_with_conditionals)

  @pytest.mark.parametrize("assignments", [dict(a=0, b=0), dict(a=0), dict(a=-1), dict()])
  def test_missing_conditionals(self, experiment_with_conditionals, assignments):
    with pytest.raises(BadParamError):
      validate_assignments_map(assignments, experiment_with_conditionals)


class TestValidateAssignmentsMapConstraints:
  @pytest.fixture
  def experiment(self):
    meta = ExperimentMeta()
    meta.all_parameters_unsorted.add(name="a")
    meta.all_parameters_unsorted.add(name="b")
    meta.all_parameters_unsorted.add(name="c")
    meta.all_parameters_unsorted.add(name="f")

    c = meta.constraints.add(
      type="greater_than",
      rhs=4,
    )
    c.terms.add(name="f", coeff=3.4234)
    c.terms.add(name="b", coeff=3)
    c = meta.constraints.add(
      type="less_than",
      rhs=44,
    )
    c.terms.add(name="f", coeff=3)
    c.terms.add(name="b", coeff=1.1)
    experiment = Experiment(experiment_meta=meta)
    return experiment

  @pytest.fixture(
    params=[
      dict(a=1, b=0, c="d", f=2),
      dict(a=1, b=-1, c="d", f=14),
    ]
  )
  def assignments(self, request):
    return request.param

  @pytest.fixture(
    params=[
      dict(a=50, b=-50, c="d", f=2),
      dict(a=25, b=-3, c="e", f=50),
    ]
  )
  def invalid_assignments(self, request):
    return request.param

  def test_valid_assignments(self, experiment, assignments):
    validate_assignments_map(assignments, experiment)

  def test_invalid_assignmnets(self, experiment, invalid_assignments):
    with pytest.raises(BadParamError):
      validate_assignments_map(invalid_assignments, experiment)
