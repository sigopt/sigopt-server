# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import numpy
import pytest
from libsigopt.sigoptaux.constant import CATEGORICAL_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME

from sigoptlite.builders import LocalObservationBuilder
from sigoptlite.models import LocalSuggestion
from sigoptlite.sources import RandomSearchSource
from sigoptlitetest.constants import ALL_META, TEST_PROB_FAILED_OBSERVATION


class UnitTestsBase(object):
  @pytest.fixture(
    params=[
      "constraints",
      "conditionals",
      "default",
      "multimetric",
      "multitask",
      "multisolution",
      "metric_constraint",
      "metric_threshold",
      "priors",
      "search",
    ]
  )
  def any_meta(self, request):
    return copy.deepcopy(ALL_META[request.param])

  @pytest.fixture
  def experiment_meta(self):
    return copy.deepcopy(ALL_META["default"])

  def get_experiment_feature(self, feature):
    assert feature in ALL_META
    return copy.deepcopy(ALL_META[feature])

  def assert_suggestion_satisfies_constraints(self, suggestion, experiment):
    if not experiment.linear_constraints:
      return

    for constraint in experiment.linear_constraints:
      lhs = sum(suggestion.assignments[term.name] * term.weight for term in constraint.terms)
      if constraint.type == "greater_than":
        assert lhs >= constraint.threshold
      else:
        assert lhs <= constraint.threshold

  def assert_valid_suggestion(self, suggestion, experiment):
    if not experiment.is_conditional:
      parameter_names = [p.name for p in experiment.parameters]
      assert all(key in parameter_names for key in suggestion.assignments.keys())
    self.assert_suggestion_satisfies_constraints(suggestion, experiment)

    for parameter in experiment.parameters:
      assignment = suggestion.assignments.get(parameter.name)
      if assignment is None:
        assert parameter.conditions
        parameter_satisfy_condition = all(
          suggestion.assignments[condition.name] in condition.values for condition in parameter.conditions
        )
        assert parameter_satisfy_condition is False
        continue
      if parameter.type == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        categorical_values_non_enum = [cv.name for cv in parameter.categorical_values]
        assert assignment in categorical_values_non_enum
      elif parameter.grid:
        assert assignment in parameter.grid
      else:
        assert assignment <= parameter.bounds.max
        assert assignment >= parameter.bounds.min
      if parameter.type == INT_EXPERIMENT_PARAMETER_NAME:
        assert int(assignment) == assignment

    for conditional in experiment.conditionals:
      assert conditional.name in suggestion.assignments
      conditional_values = [v.name for v in conditional.values]
      assert suggestion.assignments[conditional.name] in conditional_values

    if experiment.is_multitask:
      assert suggestion.task is not None
      assert suggestion.task in experiment.tasks

  def make_suggestion(self, assignments, task=None):
    return LocalSuggestion(
      assignments=assignments,
      task=task,
    )

  def make_observation(self, experiment, assignments, values=None, failed=False, task=None):
    assert bool(values) ^ failed
    observation_dict = {}
    observation_dict["assignments"] = assignments
    if values:
      observation_dict["values"] = values
    if failed:
      observation_dict["failed"] = failed
    if task:
      observation_dict["task"] = task
    return LocalObservationBuilder(observation_dict, experiment=experiment)

  def make_random_observation(self, experiment, suggestion=None):
    suggestion = self.make_random_suggestions(experiment)[0] if suggestion is None else suggestion
    task = dict(name=suggestion.task.name, cost=suggestion.task.cost) if suggestion.task else None
    failed = numpy.random.rand() <= TEST_PROB_FAILED_OBSERVATION
    values = []
    if not failed:
      values = [dict(name=m.name, value=numpy.random.rand(), value_stddev=0) for m in experiment.metrics]
    return self.make_observation(
      experiment=experiment,
      assignments=suggestion.assignments,
      values=values,
      failed=failed,
      task=task,
    )

  def make_random_suggestions(self, experiment, num_suggestions=1):
    return [RandomSearchSource(experiment).get_suggestion(observations=[]) for _ in range(num_suggestions)]

  def make_random_observations(self, experiment, num_observations=1):
    suggestions = self.make_random_suggestions(experiment, num_suggestions=num_observations)
    observations = [self.make_random_observation(experiment, suggestion) for suggestion in suggestions]
    return observations
