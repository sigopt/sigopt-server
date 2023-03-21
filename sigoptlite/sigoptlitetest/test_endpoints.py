# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest
from sigopt import Connection
import copy


from sigoptlite.driver import LocalDriver

from sigoptlitetest.base_test import UnitTestsBase


class UnitTestsEndpoint(UnitTestsBase):
  def __init__(self):
    self.conn = Connection(driver=LocalDriver)


class TestExperiment(UnitTestsEndpoint):
  def test_create_and_fetch(self, any_meta):
    experiment = self.conn.experiments().create(**any_meta)
    assert experiment.id is not None

    experiment_fetched = self.conn.experiments(experiment.id).fetch()
    assert experiment == experiment_fetched

  def test_no_observation_budget(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["observation_budget"]
    experiment = self.conn.experiments().create(**experiment_meta)
    assert experiment.observation_budget is None

  @pytest.mark.xfail  # Not being handled property atm
  def test_no_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    del experiment_meta["parameters"]
    with pytest.raises(AssertionError):
      self.conn.experiments().create(**experiment_meta)

  def test_empty_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment_meta["parameters"] = []
    with pytest.raises(AssertionError):
      self.conn.experiments().create(**experiment_meta)

  @pytest.mark.xfail  # Not being handled, should be dealt with validation refactor
  def test_experiment_create_extra_parameters(self):
    experiment_meta = self.get_experiment_feature("default")
    with pytest.raises(AssertionError):
      self.conn.experiments().create(extra_param=True, **experiment_meta)

  @pytest.mark.xfail  # Not being handled, wait for Gustavo's merge
  def test_experiment_create_wrong_parameter_types(self, any_meta):
    any_meta["parameters"][0]["type"] = "invalid_type"
    with pytest.raises(ValueError):
      self.conn.experiments().create(**any_meta)

  @pytest.mark.parametrize(
    "categorical_values",
    [["d", "e"], [dict(name="d"), dict(name="e")], [dict(name="d", enum_index=1), dict(name="e", enum_index=2)]],
  )
  def test_categorical_proper_enum_index(self, categorical_values):
    e = self.conn.experiments().create(
      parameters=[dict(name="c", type="categorical", categorical_values=["d", "e"])],
      metrics=[dict(name="y1", objective="maximize", strategy="optimize")],
    )
    (p,) = e.parameters
    (cat1, cat2) = p.categorical_values
    assert cat1.enum_index == 1
    assert cat1.name == "d"
    assert cat2.enum_index == 2
    assert cat2.name == "e"


class TestSuggestion(UnitTestsEndpoint):
  pass


class TestObservation(UnitTestsEndpoint):
  def test_create_observation_with_suggestion(self):
    experiment_meta = self.get_experiment_feature("default")
    experiment = self.conn.experiments().create(**experiment_meta)
    suggestion = self.conn.experiments(experiment.id).suggestions().create()
    value = numpy.random.rand()
    observation = (
      self.conn.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": value}])
    )
    assert observation.values[0].value == value
    assert observation.values[0].value_stddev is None
    assert observation.suggestion == suggestion.id
    assert observation.assignments == suggestion.assignments
    assert observation.created is not None
    assert observation.metadata is None
    assert observation.failed is False


class TestBestAssignments(UnitTestsBase):
  pass
