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
from zigopt.task.from_json import extract_task_from_json


class TestExtractors:
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

  def test_extract_task_from_json(self, experiment_mt):
    json_dict = {"assignments": {"x": 1.1}, "task": {"name": "a", "cost": "irrelevant"}}
    task = extract_task_from_json(experiment_mt, json_dict)
    assert task.name == "a" and task.cost == 0.1

    json_dict = {"assignments": {"x": 1.1}, "task": {"name": "a"}}
    task = extract_task_from_json(experiment_mt, json_dict)
    assert task.name == "a" and task.cost == 0.1

    json_dict = {"assignments": {"x": 1.1}, "task": {"name": "b"}}
    task = extract_task_from_json(experiment_mt, json_dict)
    assert task.name == "b" and task.cost == 1.0

    json_dict = {"assignments": {"x": 1.1}, "task": "a"}
    task = extract_task_from_json(experiment_mt, json_dict)
    assert task.name == "a" and task.cost == 0.1

    json_dict = {"task": "a"}
    task = extract_task_from_json(experiment_mt, json_dict)
    assert task.name == "a" and task.cost == 0.1

    json_dict = {"assignments": {"x": 1.1}, "wrong_tag": "a"}
    with pytest.raises(BadParamError):
      extract_task_from_json(experiment_mt, json_dict)

    json_dict = {"assignments": {"x": 1.1}, "task": "not_a_real_task"}
    with pytest.raises(BadParamError):
      extract_task_from_json(experiment_mt, json_dict)

    json_dict = {"assignments": {"x": 1.1}, "task": {"name": "not_a_real_task"}}
    with pytest.raises(BadParamError):
      extract_task_from_json(experiment_mt, json_dict)

    json_dict = {"assignments": {"x": 1.1}, "task": {"forgot_the_name": "a"}}
    with pytest.raises(BadParamError):
      extract_task_from_json(experiment_mt, json_dict)
