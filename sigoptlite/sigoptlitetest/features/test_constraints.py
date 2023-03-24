# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class TestParameterConstraints(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def base_meta(self):
    return dict(
      parameters=[
        dict(name="x0", type="double", bounds=dict(min=0, max=1)),
        dict(name="x1", type="double", bounds=dict(min=0, max=1)),
        dict(name="x2", type="int", bounds=dict(min=0, max=100)),
        dict(name="x3", type="int", bounds=dict(min=0, max=100)),
        dict(name="x4", type="categorical", categorical_values=["c1", "c2"]),
      ],
      metrics=[dict(name="metric")],
      observation_budget=10,
    )

  @pytest.fixture
  def base_constrained_meta(self):
    return dict(
      parameters=[
        dict(name="x0", type="double", bounds=dict(min=0, max=1)),
        dict(name="x1", type="double", bounds=dict(min=0, max=1)),
      ],
      linear_constraints=[
        dict(
          type="less_than",
          terms=[
            dict(name="x0", weight=1),
            dict(name="x1", weight=1),
          ],
          threshold=1,
        ),
      ],
      metrics=[dict(name="metric")],
      observation_budget=10,
    )

  def test_invalid_constraints_json(self, base_meta):
    invalid_type_meta = base_meta
    invalid_type_meta["linear_constraints"] = [
      dict(
        type="strictly_less_than",
        terms=[
          dict(name="x0", weight=1),
          dict(name="x1", weight=1),
        ],
        threshold=1,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**invalid_type_meta)
    msg = "strictly_less_than is not one of the allowed values: greater_than, less_than"
    assert exception_info.value.args[0] == msg

  def test_invalid_constraints(self, base_meta):
    invalid_name_meta = base_meta
    invalid_name_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="p0", weight=1),
          dict(name="x1", weight=1),
        ],
        threshold=1,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**invalid_name_meta)
    msg = "Variable p0 is not a known parameter"
    assert exception_info.value.args[0] == msg

    invalid_cat_term_meta = base_meta
    invalid_cat_term_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="x0", weight=1),
          dict(name="x4", weight=1),
        ],
        threshold=1,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**invalid_cat_term_meta)
    msg = "Variable x4 is not a parameter of type `double` or type `int`"
    assert exception_info.value.args[0] == msg

    invalid_term_count_meta = base_meta
    invalid_term_count_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="x0", weight=1),
        ],
        threshold=0.5,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**invalid_term_count_meta)
    msg = "Constraint must have more than one term"
    assert exception_info.value.args[0] == msg

    invalid_repeated_term_meta = base_meta
    invalid_repeated_term_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="x0", weight=1),
          dict(name="x0", weight=1),
        ],
        threshold=1,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**invalid_term_count_meta)
    msg = "Duplicate constrained variable name: x0"
    assert exception_info.value.args[0] == msg

  def test_invalid_mixed_integer_constraints(self, base_meta):
    mixed_integer_meta = base_meta
    mixed_integer_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="x1", weight=1),
          dict(name="x3", weight=1),
        ],
        threshold=3,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**mixed_integer_meta)
    msg = "Constraint functions cannot mix integers and doubles. One or the other only."
    assert exception_info.value.args[0] == msg

  def test_invalid_constraints_feature_incompatible(self, base_constrained_meta):
    grid_meta = base_constrained_meta
    grid_meta["parameters"][0] = dict(
      name="x0",
      type="double",
      grid=[0.1, 0.2, 0.4, 1.0],
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**grid_meta)
    msg = "Constraint cannot be defined on a grid parameter x0"
    assert exception_info.value.args[0] == msg

    log_transformed_meta = base_constrained_meta
    log_transformed_meta["parameters"][0] = dict(
      name="x0",
      type="double",
      bounds=dict(min=1e-4, max=1),
      transformation="log",
    )
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**log_transformed_meta)
    msg = "Constraint cannot be defined on a log-transformed parameter x0"
    assert exception_info.value.args[0] == msg

    conditional_meta = base_constrained_meta
    conditional_meta["parameters"][0] = dict(
      name="x0",
      type="double",
      bounds=dict(min=0, max=1),
      conditions=dict(con1=["true"]),
    )
    conditional_meta["conditionals"] = [
      dict(name="con1", values=["true", "false"]),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**conditional_meta)
    msg = "Constraint cannot be defined on a conditioned parameter x0"
    assert exception_info.value.args[0] == msg

  def test_infeasible_constraints(self, base_meta):
    infeasible_constraint_meta = base_meta
    infeasible_constraint_meta["linear_constraints"] = [
      dict(
        type="less_than",
        terms=[
          dict(name="x0", weight=1),
          dict(name="x1", weight=1),
        ],
        threshold=0.9,
      ),
      dict(
        type="greater_than",
        terms=[
          dict(name="x0", weight=1),
          dict(name="x1", weight=1),
        ],
        threshold=1.1,
      ),
    ]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**infeasible_constraint_meta)
    msg = "Infeasible constraints"
    assert exception_info.value.args[0] == msg
