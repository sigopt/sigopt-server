# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.config.broker import *
from zigopt.config.source import ConfigBrokerValueNotAvailableException


# pylint: disable=pointless-statement


class TestConfigBroker(object):
  def make_broker(self, sources):
    impl = ConfigBrokerImpl(sources=sources)
    broker = ConfigBroker.from_configs([])
    broker.impl = impl
    return broker

  def test_empty(self):
    broker = self.make_broker([])
    assert broker.get("fake.key", None) is None
    assert broker.get("fake.key", 1234) == 1234
    assert broker.get("fake.key", True) is True
    assert broker.get("fake.key", "abc") == "abc"

    assert broker.get("fake.key") is None
    with pytest.raises(KeyError):
      broker["fake.key"]

  def test_set(self):
    broker = self.make_broker([MutableConfigBrokerSource(), DictConfigBrokerSource({"fake": {"other": "thing"}})])
    broker["fake.key"] = "fake value"
    assert broker.get("fake.key", None) == "fake value"
    assert broker.get("fake.key", 123) == "fake value"
    assert broker["fake.key"] == "fake value"
    assert broker.get("also.fake") is None
    assert broker.get("fake.prefix") is None
    assert broker.get_object("fake") == {"key": "fake value", "other": "thing"}

  def test_not_available(self):
    source = MutableConfigBrokerSource()
    source.set_item("fake.key", "value")
    source.set_not_available("not.available.yet")
    broker = self.make_broker([source])
    assert broker["fake.key"] == "value"
    assert broker.get_object("fake") == {"key": "value"}
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker.get("not.available.yet")
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker.get("not.available.yet.subkey")
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker["not.available.yet"]
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker["not.available.yet.subkey"]
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker.get_object("not.available")
    with pytest.raises(ConfigBrokerValueNotAvailableException):
      broker.get_object("not")
    assert json.dumps(source.all_configs_for_logging()) == json.dumps(
      {"fake": {"key": "value"}, "not": {"available": {"yet": "_NOT_AVAILABLE"}}}
    )

  def test_exists(self):
    dict1 = {
      "a": {
        "a1": 1,
        "a2": True,
        "a3": "aaa",
      },
      "c": {
        "conflict": True,
        "conflict_none": None,
      },
    }
    dict2 = {
      "b": {
        "b1": 3,
        "b2": False,
        "b3": "bbb",
      },
      "c": {
        "conflict": False,
        "conflict_none": 567,
      },
    }

    broker = self.make_broker(
      [
        DictConfigBrokerSource(dict1),
        DictConfigBrokerSource(dict2),
      ]
    )

    assert broker.get("a.a1", default=None) == 1
    assert broker.get("a.a2", default=None) is True
    assert broker.get("a.a3", default=None) == "aaa"
    assert broker.get("a.a4", default=None) is None
    assert broker.get("a.a4", default="xyz") == "xyz"
    with pytest.raises(KeyError):
      broker["a.a4"]

    assert broker.get("b.b1", default=None) == 3
    assert broker.get("b.b2", default=None) is False
    assert broker.get("b.b3", default=None) == "bbb"
    assert broker.get("b.b4", default="xyz") == "xyz"
    with pytest.raises(KeyError):
      broker["b.b4"]

    assert broker.get("c.conflict", default=None) is True
    assert broker.get("c.conflict_none") is None

    assert broker.get("d", default="xyz") == "xyz"

  def test_get_object(self):
    dict1 = {
      "a": {
        "a1": 1,
        "a2": True,
        "a3": "aaa",
      },
      "c": {
        "conflict": True,
        "conflict_none": None,
      },
    }
    dict2 = {
      "b": {
        "b1": 3,
        "b2": False,
        "b3": "bbb",
      },
      "c": {
        "conflict": False,
        "conflict_none": 567,
      },
    }

    broker = self.make_broker(
      [
        DictConfigBrokerSource(dict1),
        DictConfigBrokerSource(dict2),
      ]
    )

    with pytest.raises(Exception):
      broker.get("a")
    with pytest.raises(Exception):
      broker.get("b")
    with pytest.raises(Exception):
      broker.get("c")
    assert broker.get_object("a") == {"a1": 1, "a2": True, "a3": "aaa"}
    assert broker.get_object("b") == {"b1": 3, "b2": False, "b3": "bbb"}
    assert broker.get_object("c") == {"conflict": True, "conflict_none": None}
