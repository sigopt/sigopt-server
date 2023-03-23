# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlitetest.constants import DEFAULT_METRICS_SEARCH


class TestExperimentConditionals(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.mark.parametrize("feature", ["conditionals", "multiconditional"])
  def test_create_with_conditionals(self, feature):
    meta = self.get_experiment_feature(feature)
    e = self.conn.experiments().create(**meta)
    assert e.conditionals is not None

  def test_create_parameters_with_conditions_but_no_conditionals(self):
    meta = self.get_experiment_feature("conditionals")
    del meta["conditionals"]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = (
      "For conditional sigoptlite experiment, need both conditions defined in parameters and conditionals"
      " variables defined in experiment"
    )
    assert exception_info.value.args[0] == msg

  def test_duplicate_conditionals(self):
    meta = self.get_experiment_feature("conditionals")
    meta["conditionals"] = meta["conditionals"] * 2
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    duplicate_conditionals = [c["name"] for c in meta["conditionals"]]
    msg = f"No duplicate conditionals are allowed: {duplicate_conditionals}"
    assert exception_info.value.args[0] == msg

  def test_create_conditionals_but_no_parameters_with_conditions(self):
    meta = self.get_experiment_feature("conditionals")
    for parameter in meta["parameters"]:
      parameter.pop("conditions", None)
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = (
      "For conditional sigoptlite experiment, need both conditions defined in parameters and conditionals"
      " variables defined in experiment"
    )
    assert exception_info.value.args[0] == msg

  def test_missing_conditional_value(self):
    meta = self.get_experiment_feature("multiconditional")
    missing_conditional_name = meta["conditionals"][0]["name"]
    del meta["conditionals"][0]
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = f"The parameter c has conditions {[missing_conditional_name]} that cannot be satisfied"
    assert exception_info.value.args[0] == msg

  def test_create_conditionals_parameter_condition_cannot_be_met(self):
    meta = self.get_experiment_feature("multiconditional")
    meta["parameters"][3]["conditions"] = dict(z=["not_a_real_condition_in_meta"])
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "Need at least one parameter that satisfies each conditional value"
    assert exception_info.value.args[0] == msg

  def test_multi_conditions_on_one_parameter(self):
    meta = self.get_experiment_feature("multiconditional")
    meta["parameters"][3]["conditions"] = dict(z=["on"], y=["y1"])
    self.conn.experiments().create(**meta)

  def test_experiment_conditionals_multisolution_incompatible(self):
    meta = self.get_experiment_feature("conditionals")
    meta["num_solutions"] = 3
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "sigoptlite experiment with multiple solutions does not support conditional parameters"
    assert exception_info.value.args[0] == msg

  def test_experiment_conditionals_search_incompatible(self):
    meta = self.get_experiment_feature("conditionals")
    meta["metrics"] = DEFAULT_METRICS_SEARCH
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments().create(**meta)
    msg = "All-Constraint sigoptlite experiment does not support conditional parameters"
    assert exception_info.value.args[0] == msg
