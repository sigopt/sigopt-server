# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt.exception import ApiException

from integration.v1.test_base import V1Base


class TestPriorsCreate(V1Base):
  @pytest.fixture
  def meta(self):
    return {
      "name": "prior test",
      "parameters": [
        {"name": "d", "type": "double", "bounds": {"min": 0, "max": 1}},
        {"name": "i", "type": "int", "bounds": {"min": -4, "max": 3}},
        {"name": "c", "type": "categorical", "categorical_values": [{"name": "c1"}, {"name": "c2"}]},
      ],
    }

  @pytest.mark.parametrize(
    "prior",
    [
      {"name": "normal", "mean": 0.0, "scale": 1.0},
      {"name": "beta", "shape_a": 1.0, "shape_b": 1.0},
    ],
  )
  def test_create_with_priors(self, connection, meta, prior):
    meta["parameters"][0]["prior"] = prior
    connection.clients(connection.client_id).experiments().create(**meta)

  @pytest.mark.parametrize(
    "prior",
    [
      {"name": "normal", "mean": 0.0, "scale": -1.0},
      {"name": "beta", "shape_a": 0.0, "shape_b": 1.0},
    ],
  )
  def test_create_with_invalid_priors(self, connection, meta, prior):
    meta["parameters"][0]["prior"] = prior

    with pytest.raises(ApiException):
      connection.clients(connection.client_id).experiments().create(**meta)
