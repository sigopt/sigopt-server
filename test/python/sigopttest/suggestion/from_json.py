# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_DOUBLE,
  Bounds,
  ExperimentMeta,
  ExperimentParameter,
  Task,
)
from zigopt.suggestion.from_json import build_suggestion_data_from_json

from libsigopt.aux.errors import InvalidTypeError


class TestBuildSuggestionData(object):
  @pytest.fixture
  def experiment(self):
    return Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name="x", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=1, maximum=2)),
        ],
      )
    )

  @pytest.fixture
  def experiment_mt(self):
    return Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name="x", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=1, maximum=2)),
        ],
        tasks=[Task(name="a", cost=0.1), Task(name="b", cost=1.0)],
      )
    )

  def test_build_suggestion_data_from_json(self, experiment, experiment_mt):
    json_dict = {"assignments": {"x": 1.1}}
    suggestion_data = build_suggestion_data_from_json(experiment, json_dict)
    assert suggestion_data.assignments_map == json_dict["assignments"]

    json_dict = {"assignments": {"x": 1.1}, "extra_irrelevant_stuff": True}
    suggestion_data = build_suggestion_data_from_json(experiment, json_dict)
    assert suggestion_data.assignments_map == json_dict["assignments"]

    json_dict = {"assignments": {"x": "wrong assignments"}}
    with pytest.raises(InvalidTypeError):
      build_suggestion_data_from_json(experiment, json_dict)

    json_dict = {"assignments": {"x": 1.1, "what_is_this_parameter": 12345}}
    with pytest.raises(BadParamError):
      build_suggestion_data_from_json(experiment, json_dict)

    json_dict = {"assignments": {"x": 1.1}, "task": {"name": "a"}}
    suggestion_data = build_suggestion_data_from_json(experiment_mt, json_dict)
    assert suggestion_data.assignments_map == json_dict["assignments"]
    assert suggestion_data.task.name == "a" and suggestion_data.task.cost == 0.1
