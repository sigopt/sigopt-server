# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
from typing import Any

from zigopt.common import *


class _NotAvailableClass:
  def __repr__(self) -> str:
    return "NotAvailable"


_NOT_AVAILABLE = _NotAvailableClass()


class ConfigBrokerSource:
  supports_types = True

  def _split_name(self, name: str) -> list[str]:
    return name.split(".")

  def __contains__(self, name: str) -> bool:
    raise NotImplementedError()

  def get(self, name: str, default: Any = None) -> Any:
    raise NotImplementedError()

  def all_configs_for_logging(self) -> None:
    raise NotImplementedError()


class DecoratorConfigBrokerSource(ConfigBrokerSource):
  def __init__(self, underlying: ConfigBrokerSource):
    super().__init__()
    self.underlying = underlying

  def __contains__(self, name: str) -> bool:
    return self.underlying.__contains__(name)

  def get(self, name: str, default: Any = None) -> Any:
    return self.underlying.get(name, default=default)

  def all_configs_for_logging(self) -> None:
    return self.underlying.all_configs_for_logging()


class MutableConfigBrokerSource(DecoratorConfigBrokerSource):
  def __init__(self):
    data = {}
    super().__init__(DictConfigBrokerSource(data))
    self._dict = data

  def set_item(self, name: str, value: Any) -> None:
    parts = self._split_name(name)
    base_dict = self._dict
    for p in parts[:-1]:
      base_dict = base_dict.setdefault(p, {})
      if not is_mapping(base_dict):
        raise Exception(f"Expected object for key {p} in {name} - found {type(base_dict)}")
    base_dict[parts[-1]] = value

  def set_not_available(self, name: str) -> None:
    self.set_item(name, _NOT_AVAILABLE)

  def reset(self) -> None:
    self._dict.clear()


class EnvironmentConfigBrokerSource(DecoratorConfigBrokerSource):
  supports_types = False

  def __init__(self):
    super().__init__(MutableConfigBrokerSource())
    for k, v in os.environ.items():
      prefix = "sigopt."
      if k.startswith(prefix):
        k = k[len(prefix) :]
        self.underlying.set_item(k, v)


class ConfigBrokerValueNotAvailableException(KeyError):
  pass


class DictConfigBrokerSource(ConfigBrokerSource):
  supports_types = True

  def __init__(self, d: dict[str, Any]):
    super().__init__()
    self.d = d

  def __contains__(self, name: str) -> bool:
    return self._do_get(name, default=None)[0]

  def get(self, name: str, default: Any = None) -> Any:
    return self._do_get(name, default)[1]

  def all_configs_for_logging(self) -> None:
    return self._remove_unavailable(self.d)

  def _remove_unavailable(self, value: Any) -> Any:
    if is_mapping(value):
      return {k: "_NOT_AVAILABLE" if v is _NOT_AVAILABLE else self._remove_unavailable(v) for k, v in value.items()}
    return value

  def _do_get(self, name: str, default: Any) -> tuple[bool, Any]:
    # Returns a tuple (did_contain, value), so we can distinguish between
    # null being explicitly present or not

    base_dict: Any = self.d
    parts = self._split_name(name)

    for p in parts[:-1]:
      base_dict = base_dict.get(p)
      if base_dict is _NOT_AVAILABLE:
        raise ConfigBrokerValueNotAvailableException()
      if not is_mapping(base_dict):
        return (False, None)

    if is_mapping(base_dict):
      did_contain = parts[-1] in base_dict
      value = base_dict.get(parts[-1], default)
      self._raise_on_not_available(value)
      return (did_contain, value)
    else:
      return (False, None)

  def _raise_on_not_available(self, value: Any) -> None:
    if value is _NOT_AVAILABLE:
      raise ConfigBrokerValueNotAvailableException()
    if is_mapping(value):
      for v in value.values():
        self._raise_on_not_available(v)
