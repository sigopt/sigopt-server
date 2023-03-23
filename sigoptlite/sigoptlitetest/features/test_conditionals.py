import pytest

from sigoptlitetest.base_test import UnitTestsBase
from sigoptlite.driver import LocalDriver
from sigopt import Connection


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
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_duplicate_conditionals(self):
    meta = self.get_experiment_feature("conditionals")
    meta["conditionals"] = meta["conditionals"] * 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_create_conditionals_but_no_parameters_with_conditions(self):
    meta = self.get_experiment_feature("conditionals")
    for parameter in meta["parameters"]:
      parameter.pop("conditions", None)
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_missing_conditional_value(self):
    meta = self.get_experiment_feature("multiconditional")
    del meta["conditionals"][0]
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_create_conditionals_parameter_condition_cannot_be_met(self):
    meta = self.get_experiment_feature("multiconditional")
    meta["parameters"][3]["conditions"] = dict(z=["not_a_real_condition_in_meta"])
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_no_conditionals_with_multisolution(self):
    meta = self.get_experiment_feature("conditionals")
    meta["num_solutions"] = 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)

  def test_no_conditionals_with_search(self):
    meta = self.get_experiment_feature("search")
    meta["num_solutions"] = 2
    with pytest.raises(ValueError):
      self.conn.experiments().create(**meta)
