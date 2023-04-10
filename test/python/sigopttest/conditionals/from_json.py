# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.conditionals.from_json import set_conditional_from_json, set_experiment_conditionals_list_from_json
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentConditional, ExperimentMeta

from libsigopt.aux.errors import InvalidValueError, MissingJsonKeyError


class TestSetConditionalFromJson:
  @pytest.fixture
  def conditional(self):
    return ExperimentConditional()

  def test_set_conditional_from_json(self, conditional):
    set_conditional_from_json(conditional, dict(name="x", values=["1", "5", "10"]))
    assert conditional.name == "x"
    assert sorted([v.name for v in conditional.values]) == sorted(["1", "5", "10"])
    assert sorted([v.enum_index for v in conditional.values]) == [1, 2, 3]

  def test_duplicate_values(self, conditional):
    with pytest.raises(InvalidValueError):
      set_conditional_from_json(conditional, dict(name="x", values=["1", "1"]))

  def test_missing_name(self, conditional):
    with pytest.raises(MissingJsonKeyError):
      set_conditional_from_json(conditional, dict(values=["1", "5", "10"]))

  @pytest.mark.parametrize(
    "conditional_json",
    [
      dict(name="x"),
    ],
  )
  def test_too_few_values(self, conditional, conditional_json):
    with pytest.raises(MissingJsonKeyError):
      set_conditional_from_json(conditional, conditional_json)

  @pytest.mark.parametrize(
    "conditional_json",
    [
      dict(name="x", values=[]),
      dict(name="x", values=["1"]),
    ],
  )
  def test_too_few_values_bad_param(self, conditional, conditional_json):
    with pytest.raises(BadParamError):
      set_conditional_from_json(conditional, conditional_json)


class TestSetConditionalsListFromJson:
  @pytest.fixture
  def experiment_meta(self):
    return ExperimentMeta()

  def test_set_experiment_conditionals_list_from_json(self, experiment_meta):
    experiment_json = dict(conditionals=[dict(name="x", values=["1", "5", "10"])])
    set_experiment_conditionals_list_from_json(experiment_meta, experiment_json)
    (conditional,) = experiment_meta.conditionals
    assert conditional.name == "x"
    assert sorted([v.name for v in conditional.values]) == sorted(["1", "5", "10"])
    assert sorted([v.enum_index for v in conditional.values]) == [1, 2, 3]

  @pytest.mark.parametrize(
    "experiment_json",
    [
      dict(),
      dict(conditionals=[]),
    ],
  )
  def test_empty_conditionals_json(self, experiment_meta, experiment_json):
    set_experiment_conditionals_list_from_json(experiment_meta, experiment_json)
    assert len(experiment_meta.conditionals) == 0

  def test_duplicate_names(self, experiment_meta):
    with pytest.raises(BadParamError):
      experiment_json = dict(
        conditionals=[
          dict(name="x", values=["10", "25"]),
          dict(name="x", values=["1", "5"]),
        ]
      )
      set_experiment_conditionals_list_from_json(experiment_meta, experiment_json)
