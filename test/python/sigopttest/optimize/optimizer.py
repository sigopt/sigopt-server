# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-
import functools
import operator

from flaky import flaky
from mock import Mock

from zigopt.experiment.constant import CATEGORICAL_EXPERIMENT_PARAMETER_NAME
from zigopt.optimize.categorical import all_categorical_value_combos
from zigopt.optimize.optimizer import OptimizerService
from zigopt.parameters.from_json import set_experiment_parameter_from_json
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  ExperimentCategoricalValue,
  ExperimentMeta,
  ExperimentParameter,
)

from sigopttest.base.utils import partial_opt_args
from sigopttest.optimize.sources.base_test import UnitTestBase


class TestAllCategoricalValueCombos:
  valid_param_names = ["param1", "param2", "param3"]
  param_data = {
    "parameters": [
      {
        "name": valid_param_names[0],
        "type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
        "categorical_values": [
          {"name": "some"},
          {"name": "thing"},
          {"name": "cool"},
        ],
      },
      {
        "name": valid_param_names[1],
        "type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
        "categorical_values": [
          {"name": "first"},
          {"name": "second"},
        ],
      },
      {
        "name": valid_param_names[2],
        "type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
        "categorical_values": [
          {"name": "whoa"},
          {"name": "omg"},
          {"name": "wow"},
        ],
      },
    ],
  }

  def test_no_categorical_params(self):
    all_combos = list(all_categorical_value_combos([]))
    assert len(all_combos) == 1
    assert len(all_combos[0]) == 0

  def test_one_categorical_param(self):
    parameter = ExperimentParameter()
    set_experiment_parameter_from_json(
      parameter,
      self.param_data["parameters"][0],
      ExperimentMeta.OFFLINE,
      dict(),
    )
    categorical_parameters = [parameter]

    all_combos = list(all_categorical_value_combos(categorical_parameters))

    # all combos is just all values of this category
    assert all(len(cat_value) == 1 for cat_value in all_combos)
    all_values_truth = set(cat_value.enum_index for cat_value in categorical_parameters[0].all_categorical_values)
    all_values_test = set(list(cat_value)[0][1] for cat_value in all_combos)

    assert all_values_truth == all_values_test

  def test_many_categorical_params(self):
    categorical_parameters = []
    for parameter_json in self.param_data["parameters"]:
      parameter = ExperimentParameter()
      set_experiment_parameter_from_json(
        parameter,
        parameter_json,
        ExperimentMeta.OFFLINE,
        dict(),
      )
      categorical_parameters.append(parameter)

    all_combos = list(all_categorical_value_combos(categorical_parameters))

    all_names = set(param.name for param in categorical_parameters)
    seen_combos = set()

    num_combos = functools.reduce(
      operator.mul,
      [len(cat_param["categorical_values"]) for cat_param in self.param_data["parameters"]],
      1,
    )
    assert len(all_combos) == num_combos

    for combo in all_combos:
      # check all categorical parameter names represented
      names = set(c[0] for c in combo)
      assert all_names == names

      # check combo is unique
      assert combo not in seen_combos
      seen_combos.add(combo)

  def test_categorical_param_with_one_category(self):
    """Test that a categorical w/only 1 option shows up as itself in every combo."""
    categorical_parameters = []
    for parameter_json in self.param_data["parameters"]:
      parameter = ExperimentParameter()
      set_experiment_parameter_from_json(
        parameter,
        parameter_json,
        ExperimentMeta.OFFLINE,
        dict(),
      )
      categorical_parameters.append(parameter)

    all_combos = list(all_categorical_value_combos(categorical_parameters))

    new_param = ExperimentParameter()
    new_param.name = "zzzz"
    new_param.param_type = PARAMETER_CATEGORICAL
    new_cat = ExperimentCategoricalValue()
    new_cat.name = "single_cat"
    new_cat.enum_index = 1
    new_param.all_categorical_values.extend([new_cat])

    all_combos_with_single_cat = all_categorical_value_combos(categorical_parameters + [new_param])

    for combo, combo_with_single in zip(all_combos, all_combos_with_single_cat):
      combo_with_single = set(combo_with_single)
      combo_with_single.remove(("zzzz", 1))
      assert combo == combo_with_single


class TestOptimizer(UnitTestBase):
  @flaky(max_runs=2)
  def test_exclude_duplicate_suggestions_edge_cases(self, services, experiment):
    optimizer = OptimizerService(services=Mock())

    # No observations, no open_suggestions
    new_suggestions = self.sample_suggestions(services, experiment, 6)
    acceptable_solutions = optimizer.exclude_duplicate_suggestions(partial_opt_args(), new_suggestions, experiment)
    assert len(acceptable_solutions) == len(new_suggestions)

    # No observations, with open_suggestions
    optimization_args = partial_opt_args(open_suggestions=new_suggestions[1:4])
    acceptable_solutions = optimizer.exclude_duplicate_suggestions(optimization_args, new_suggestions, experiment)
    assert len(acceptable_solutions) == len(new_suggestions) - len(optimization_args.open_suggestions)

    optimization_args = partial_opt_args(open_suggestions=self.sample_suggestions(services, experiment, 3))
    acceptable_solutions = optimizer.exclude_duplicate_suggestions(optimization_args, new_suggestions, experiment)
    assert len(acceptable_solutions) == len(new_suggestions)

    # No suggestions
    acceptable_solutions = optimizer.exclude_duplicate_suggestions(optimization_args, [], experiment)
    assert len(acceptable_solutions) == 0

    acceptable_solutions = optimizer.exclude_duplicate_suggestions(partial_opt_args(), [], experiment)
    assert len(acceptable_solutions) == 0

    suggestions_for_observations = self.sample_suggestions(services, experiment, 20)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions_for_observations)
    optimization_args = partial_opt_args(
      observation_iterator=observations,
      observation_count=len(observations),
      open_suggestions=self.sample_suggestions(services, experiment, 3),
    )
    acceptable_solutions = optimizer.exclude_duplicate_suggestions(optimization_args, [], experiment)
    assert len(acceptable_solutions) == 0

  # TODO: Make this test more extensive
  @flaky(max_runs=2)
  def test_exclude_duplicate_suggestions(self, services, experiment):
    optimizer = OptimizerService(services=Mock())

    suggestions_for_observations = self.sample_suggestions(services, experiment, 20)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions_for_observations)

    # There is basically zero chance this can create a duplicate outcome
    new_suggestions = self.sample_suggestions(services, experiment, 6)

    args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    only_unique_new_suggestions = optimizer.exclude_duplicate_suggestions(args, new_suggestions, experiment)
    assert len(only_unique_new_suggestions) == len(new_suggestions)

    suggestions_to_exclude = self.form_random_observations_from_suggestions(experiment, new_suggestions)
    args = partial_opt_args(
      observation_iterator=observations + suggestions_to_exclude,
      observation_count=len(observations) + len(suggestions_to_exclude),
    )
    only_unique_new_suggestions = optimizer.exclude_duplicate_suggestions(args, new_suggestions, experiment)
    assert len(only_unique_new_suggestions) == 0

    args = partial_opt_args(
      observation_iterator=observations,
      observation_count=len(observations),
      open_suggestions=new_suggestions[2:4],
    )
    only_unique_new_suggestions = optimizer.exclude_duplicate_suggestions(args, new_suggestions, experiment)
    assert len(only_unique_new_suggestions) == len(new_suggestions) - len(args.open_suggestions)

    suggestions_to_exclude = self.form_random_observations_from_suggestions(experiment, new_suggestions[1:3])
    args = partial_opt_args(
      observation_iterator=observations + suggestions_to_exclude,
      observation_count=len(observations) + len(suggestions_to_exclude),
      open_suggestions=new_suggestions[3:],
    )
    only_unique_new_suggestions = optimizer.exclude_duplicate_suggestions(args, new_suggestions, experiment)
    assert len(only_unique_new_suggestions) == 1
