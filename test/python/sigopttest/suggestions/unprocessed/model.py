# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random
from enum import Enum, auto

import pytest

from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class BoundType(Enum):
  test_MIN = auto()
  test_MAX = auto()


class TestIsValid:
  @pytest.fixture
  def parameters(self):
    return [
      ExperimentParameter(
        name="a",
        param_type=PARAMETER_CATEGORICAL,
        all_categorical_values=[
          ExperimentCategoricalValue(name="foo", enum_index=1),
          ExperimentCategoricalValue(name="bar", enum_index=2, deleted=True),
          ExperimentCategoricalValue(name="baz", enum_index=3),
        ],
      ),
      ExperimentParameter(
        name="b",
        param_type=PARAMETER_DOUBLE,
        bounds=Bounds(minimum=-2.2, maximum=2.2),
      ),
      ExperimentParameter(
        name="c",
        param_type=PARAMETER_DOUBLE,
        bounds=Bounds(minimum=0, maximum=1),
      ),
      ExperimentParameter(
        name="d",
        param_type=PARAMETER_INT,
        bounds=Bounds(minimum=-2, maximum=0),
      ),
      ExperimentParameter(
        name="e",
        param_type=PARAMETER_DOUBLE,
        grid_values=[-0.2, -0.1, 0.2, 0.6, 1.4],
      ),
    ]

  def get_random_value(self, parameter):
    if parameter.param_type == PARAMETER_CATEGORICAL:
      return random.choice([v.enum_index for v in parameter.all_categorical_values if not v.deleted])
    if parameter.grid_values:
      return random.choice(parameter.grid_values)
    minimum, maximum = parameter.bounds.minimum, parameter.bounds.maximum
    if parameter.param_type == PARAMETER_DOUBLE:
      return random.uniform(minimum, maximum)
    if parameter.param_type == PARAMETER_INT:
      return random.randint(int(minimum), int(maximum))
    raise ValueError(f"unknown param_type {parameter.param_type}")

  def get_bound_value(self, parameter, bound):
    if bound not in BoundType:
      raise ValueError(f"bound must be BoundType, not {repr(bound)}")
    if parameter.param_type == PARAMETER_CATEGORICAL:
      func = max if bound == BoundType.test_MAX else min
      return func(v.enum_index for v in parameter.all_categorical_values if not v.deleted)
    if parameter.grid_values:
      func = max if bound == BoundType.test_MAX else min
      return func(parameter.grid_values)
    if parameter.param_type in (PARAMETER_DOUBLE, PARAMETER_INT):
      return parameter.bounds.maximum if bound == "max" else parameter.bounds.minimum
    raise ValueError(f"unknown param_type {parameter.param_type}")

  @pytest.fixture
  def experiment(self, parameters):
    return Experiment(experiment_meta=ExperimentMeta(all_parameters_unsorted=parameters))

  def make_suggestion_from_assignments(self, assignments):
    return UnprocessedSuggestion(
      suggestion_meta=SuggestionMeta(
        suggestion_data=SuggestionData(
          assignments_map=assignments,
        ),
      ),
    )

  def test_is_valid(self, experiment, parameters):
    suggestion = self.make_suggestion_from_assignments(
      {parameter.name: self.get_random_value(parameter) for parameter in parameters}
    )
    assert suggestion.is_valid(experiment) is True

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=1, b=0, c=0.5, d=-0.5, e=0.2),
    ],
  )
  def test_float_for_int_param_is_valid(self, experiment, assignments):
    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is True

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=2, b=-2.2, c=0, d=-2, e=0.6),
      dict(a=1, b=-3, c=1, d=0, e=0.2),
      dict(a=1, b=0, c=-1, d=-1, e=1.4),
      dict(a=1, b=0, c=1, d=-1, e=0),
    ],
  )
  def test_out_of_bounds_is_invalid(self, experiment, assignments):
    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is False

  def test_bounds_are_valid(self, experiment, parameters):
    assignments = {parameter.name: self.get_random_value(parameter) for parameter in parameters}
    for bound in BoundType:
      for parameter in parameters:
        assignments_copy = assignments.copy()
        assignments_copy[parameter.name] = self.get_bound_value(parameter, bound)
        suggestion = self.make_suggestion_from_assignments(assignments_copy)
        assert (
          suggestion.is_valid(experiment) is True
        ), f'failed testing {bound} "{parameter.name}" with value {assignments_copy[parameter.name]}'

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=2, b=-2.2, c=0, d=-2, e=0.6),
      dict(a=2, b=-50, c=-50, d=-50, e=0.2),
    ],
  )
  def test_deleted_catgorical_param_is_invalid(self, experiment, assignments):
    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is False

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=1, b=-2.2, c=0, d=-2, e=-0.2, f=0),
      dict(a=1, b=-2.2, c=0, d=-2, e=-0.1, f=0.2),
      dict(a=1, b=-2.2, c=0, d=-2, e=1.4, f=-2),
    ],
  )
  def test_extra_assignment(self, experiment, assignments):
    """
        This case occurs when an experiment deletes a parameter after suggestions have been generated
        """
    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is True

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=1, b=-2.2, c=0, e=-0.2),
      dict(a=1, b=2.2, d=0, e=-0.1),
      dict(a=1, c=0.5, d=-1, e=0.6),
      dict(b=-2.2, c=0.5, d=-1, e=1.4),
      dict(a=3, b=0, c=0.1, d=-2),
    ],
  )
  def test_missing_assignment(self, parameters, assignments):
    """
        This case occurs when an experiment adds a parameter after suggestions have been generated
        """
    for parameter in parameters:
      if parameter.HasField("bounds"):
        parameter.replacement_value_if_missing = parameter.bounds.minimum
      elif parameter.grid_values:
        parameter.replacement_value_if_missing = random.choice(parameter.grid_values)
      else:
        parameter.replacement_value_if_missing = 1

    experiment = Experiment(experiment_meta=ExperimentMeta(all_parameters_unsorted=parameters))

    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is True

  @pytest.mark.parametrize(
    "assignments",
    [
      dict(a=1, b=-2.2, c=0, d=-2, e=0.2, f=0),
      dict(a=1, b=-2.2, c=0, d=-2, e=-0.2, f=1),
      dict(a=1, b=-2.2, c=0, d=-2, e=1.4, f=2),
    ],
  )
  def test_conditionals_are_ignored(self, parameters, assignments):
    conditional = ExperimentConditional(
      name="f",
      values=[ExperimentConditionalValue(name="c1", enum_index=1)],
    )

    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        conditionals=[conditional],
        all_parameters_unsorted=parameters,
      )
    )

    suggestion = self.make_suggestion_from_assignments(assignments)
    assert suggestion.is_valid(experiment) is True
