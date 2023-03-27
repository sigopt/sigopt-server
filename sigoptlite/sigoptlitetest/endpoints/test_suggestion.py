import pytest
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase
from sigoptlite.models import FIXED_EXPERIMENT_ID


class TestSuggestionCreate(UnitTestsBase):
  conn = Connection(driver=LocalDriver)

  @pytest.fixture
  def experiment_meta(self):
    return self.get_experiment_feature("default")

  def test_suggestion_duplicates(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    s1 = self.conn.experiments(e.id).suggestions().create()
    s2 = self.conn.experiments(e.id).suggestions().create()
    assert s1 == s2

  def test_wrong_suggestion_id(self, experiment_meta):
    e = self.conn.experiments().create(**experiment_meta)
    s = self.conn.experiments(e.id).suggestions().create()
    with pytest.raises(ValueError) as exception_info:
      self.conn.experiments(e.id).observations().create(
        suggestion=s.id + "1",
        values=[{"name": "y1", "value": 1}],
      )
    msg = f"The suggestion you provided: {s.id + '1'} does not match the suggestion stored: {s.id}"
    assert exception_info.value.args[0] == msg

  def test_no_suggestion_id(self, experiment_meta):
    self.conn.experiments().create(**experiment_meta)
    with pytest.raises(Exception) as exception_info:
      self.conn.experiments().suggestions().fetch()
    msg = "Please provide an Experiment ID."
    assert exception_info.value.args[0] == msg

  def test_suggestion_create_before_experiment_create(self):
    new_conn = Connection(driver=LocalDriver)
    with pytest.raises(ValueError) as exception_info:
      new_conn.experiments(FIXED_EXPERIMENT_ID).suggestions().create()
    msg = "Need to create an experiment first before creating a suggestion"
    assert exception_info.value.args[0] == msg
