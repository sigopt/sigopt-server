# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_METRICS


class TestExperimentPriors(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  def test_priors_basic(self):
    meta = self.get_experiment_feature("priors")
    e = self.conn.experiments().create(**meta)
    assert e.parameters[0].prior is not None
    assert e.parameters[0].prior.name == meta["parameters"][0]["prior"]["name"]
    assert e.parameters[2].prior is not None
    assert e.parameters[2].prior.name == meta["parameters"][2]["prior"]["name"]

  def test_priors_non_double_forbidden(self):
    meta = dict(
      parameters=[
        dict(
          name="int_beta",
          type="int",
          bounds=dict(min=0, max=10),
          prior=dict(name="beta", shape_a=1, shape_b=2),
        )
      ],
      metrics=DEFAULT_METRICS,
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "Prior only applies to parameters type of double"
    assert exception_info.value.args[0] == msg

    meta["parameters"] = [
      dict(
        name="categorical_beta",
        type="categorical",
        categorical_values=["0", "5", "10"],
        prior=dict(name="beta", shape_a=1, shape_b=2),
      )
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    assert exception_info.value.args[0] == msg

  def test_priors_grid_forbidden(self):
    meta = dict(
      parameters=[
        dict(
          name="grid_beta",
          type="double",
          grid=[0.1, 0.2, 0.4, 0.5, 1.0],
          prior=dict(name="beta", shape_a=1, shape_b=2),
        )
      ],
      metrics=DEFAULT_METRICS,
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "Grid parameters cannot have priors"
    assert exception_info.value.args[0] == msg

  def test_priors_log_transformation_forbidden(self):
    meta = dict(
      parameters=[
        dict(
          name="log_transform_beta",
          type="double",
          bounds=dict(min=1e-5, max=1e-2),
          prior=dict(name="beta", shape_a=1, shape_b=2),
          transformation="log",
        )
      ],
      metrics=DEFAULT_METRICS,
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "Parameters with log transformation cannot have priors"
    assert exception_info.value.args[0] == msg
