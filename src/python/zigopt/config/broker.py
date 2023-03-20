# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import os
from typing import Any, Callable, Optional, Sequence, TypeVar

import yaml

from zigopt.common import *
from zigopt.common.conversions import user_input_to_bool
from zigopt.config.source import (
  ConfigBrokerSource,
  DictConfigBrokerSource,
  EnvironmentConfigBrokerSource,
  MutableConfigBrokerSource,
)


config_broker_T = TypeVar("config_broker_T")

_NO_DEFAULT = object()
DEFAULT_SIGOPT_CONFIG_DIR = "./config"
SIGOPT_CONFIG_DIR_ENV_KEY = "sigopt_server_config_dir"


class ConfigBroker(object):
  def __init__(self, sources: Sequence["ConfigBrokerSource"]):
    error_message = (
      "Sources must be a list of ConfigBrokerSources. Hint: you might want one of the ConfigBroker.from_* classmethods"
    )
    assert isinstance(sources, list), error_message
    sources = remove_nones_sequence(sources, list)
    assert all(isinstance(source, ConfigBrokerSource) for source in sources), error_message
    self.mutable_source = MutableConfigBrokerSource()
    self.sources = [self.mutable_source, *sources]
    self.impl = ConfigBrokerImpl(self.sources)

  def get(self, name: str, default: Any = None) -> Any:
    return self.impl.get(name, default)

  def get_object(self, name: str, default: Any = None) -> Optional[dict[str, Any]]:
    return self.impl.get_object(name, default)

  def get_array(self, name: str, default: Optional[list] = None) -> Optional[list]:
    return self.impl.get_array(name, default)

  def get_int(self, name: str, default: Optional[int] = None) -> Optional[int]:
    return self.impl.get_int(name, default)

  def get_bool(self, name: str, default: Optional[bool] = None) -> Optional[bool]:
    return self.impl.get_bool(name, default)

  def get_string(self, name: str, default: Optional[str] = None) -> Optional[str]:
    return self.impl.get_string(name, default)

  def log_configs(self) -> None:
    for source in self.impl.sources:
      logging.getLogger("sigopt.config").info(
        "%s %s",
        source.__class__.__name__,
        json.dumps(source.all_configs_for_logging()),
      )

  @classmethod
  def from_configs(cls, configs: Sequence[dict] | dict) -> "ConfigBroker":
    configs_ = [configs] if isinstance(configs, dict) else configs
    sources = [
      *(DictConfigBrokerSource(c) for c in configs_),
      EnvironmentConfigBrokerSource(),
    ]

    return cls(sources)

  @classmethod
  def from_file(cls, filename: str) -> "ConfigBroker":
    configs = []
    extends = filename
    while extends:
      extends = os.path.abspath(extends)
      try:
        with open(extends, "r") as config_fp:
          config = yaml.safe_load(config_fp)
      except OSError as ose:
        raise Exception(f"Error when loading config file {extends}") from ose
      original = extends
      extends = config.pop("extends", None)
      assert isinstance(
        extends, (str, type(None))
      ), f"The extends section for {original} should be a string, got {type(extends).__name__}"
      configs.append(config)
      if extends is not None:
        basedir = os.environ.get(SIGOPT_CONFIG_DIR_ENV_KEY, DEFAULT_SIGOPT_CONFIG_DIR)
        if extends.startswith("./") or extends.startswith("../"):
          basedir = os.path.dirname(original)
        extends = os.path.join(basedir, extends)
    return cls.from_configs(configs)

  def __getitem__(self, name: str) -> Any:
    ret = self.impl.get(name, _NO_DEFAULT)
    if ret == _NO_DEFAULT:
      raise KeyError(name)
    return ret

  def __setitem__(self, name: str, value: Any) -> None:
    self.impl.set_item(name, value)

  def reset(self) -> None:
    self.mutable_source.reset()


class ConfigBrokerImpl(object):
  def __init__(self, sources):
    self.sources = sources

  def get(self, name: str, default: Any) -> Any:
    return self._get(name, default)[0]

  def _get(self, name: str, default: Any) -> Any:
    for source in self.sources:
      if name in source:
        ret = source.get(name, default)
        self._ensure_safe_return(ret)
        return ret, source
    return default, None

  def get_int(self, name: str, default: Optional[int]) -> Optional[int]:
    return self._typed_get(name, default, int)

  def get_bool(self, name: str, default: Optional[bool]) -> Optional[bool]:
    return self._typed_get(name, default, bool, user_input_to_bool)

  def get_string(self, name: str, default: Optional[str]) -> Optional[str]:
    return self._typed_get(name, default, str, str)

  def get_array(self, name: str, default: Optional[list]) -> Optional[list]:
    return self._typed_get(name, default, list)

  def _typed_get(
    self,
    name: str,
    default: Optional[config_broker_T],
    typ: type[config_broker_T],
    transformer: Optional[Callable[[Any], config_broker_T]] = None,
  ) -> Optional[config_broker_T]:
    val, source = self._get(name, default)
    if source and not source.supports_types:
      val = (transformer or typ.__call__)(val)
    if val is not None:
      assert isinstance(val, typ)
    return val

  def get_object(self, name: str, default: Optional[dict]) -> Optional[dict]:
    objs = []
    for source in self.sources:
      if name in source:
        our_default = object()
        ret = source.get(name, our_default)
        assert ret is not our_default
        objs.append(ret)
    return extend_dict({}, *reversed(objs)) if objs else default

  def _ensure_safe_return(self, val: Any) -> None:
    if is_mapping(val):
      raise Exception("Possibly unsafe .get of mapping, values might be missing. Please use .get_object instead")

  def set_item(self, name: str, value: Any) -> None:
    if self.sources:
      self.sources[0].set_item(name, value)
