# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Tests for dict-like utils with extra validation."""
import copy

import pytest

from zigopt.handlers.validate.experiment import validate_experiment_json_dict_for_create
from zigopt.net.errors import InvalidValueError


OK_NAME = "name"
SHORT_NAME = ""
LONG_NAME = "name" * 100


class TestValidateExperimentJsonForCreate(object):
  @pytest.fixture
  def valid_experiment(self):
    return {"name": OK_NAME, "type": "offline", "metrics": [{"name": OK_NAME}], "parameters": [{"name": OK_NAME}]}

  def test_valid_json(self, valid_experiment):
    validate_experiment_json_dict_for_create(valid_experiment)

  def test_invalid_experiment_name(self, valid_experiment):
    invalid_experiment = copy.deepcopy(valid_experiment)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["name"] = SHORT_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "greater than" in str(e.value)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["name"] = LONG_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "less than" in str(e.value)

  def test_invalid_metric_name(self, valid_experiment):
    invalid_experiment = copy.deepcopy(valid_experiment)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["metrics"][0]["name"] = SHORT_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "greater than" in str(e.value)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["metrics"][0]["name"] = LONG_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "less than" in str(e.value)

  def test_invalid_parameter_name(self, valid_experiment):
    invalid_experiment = copy.deepcopy(valid_experiment)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["parameters"][0]["name"] = SHORT_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "greater than" in str(e.value)
    with pytest.raises(InvalidValueError) as e:
      invalid_experiment["parameters"][0]["name"] = LONG_NAME
      validate_experiment_json_dict_for_create(invalid_experiment)
    assert "less than" in str(e.value)

  def test_no_metric(self, valid_experiment):
    valid_experiment = copy.deepcopy(valid_experiment)
    valid_experiment["metrics"] = None
    validate_experiment_json_dict_for_create(valid_experiment)
    del valid_experiment["metrics"]
    validate_experiment_json_dict_for_create(valid_experiment)

  def test_minimal_required(self):
    validate_experiment_json_dict_for_create({"name": OK_NAME, "parameters": [{"name": OK_NAME}]})
