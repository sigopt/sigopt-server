# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.config.broker import ConfigBroker


class StrictAccessConfigBroker(ConfigBroker):
  """
    A config broker that will error if you reference an unknown key.
    Useful to enforce that all config keys are defined explicitly in the test,
    rather than falling back to defaults
    """

  def get(self, name, default=None):
    return self._safe_get(name, "get")

  def _safe_get(self, name, method_name):
    default = object()
    ret = getattr(super(), method_name)(name, default=default)
    if ret == default:
      raise Exception(f"Config value for {name} has not been specified.")
    return ret

  def get_object(self, name, default=None):
    return self._safe_get(name, "get_object")

  def get_array(self, name, default=None):
    return self._safe_get(name, "get_array")

  def get_int(self, name, default=None):
    return self._safe_get(name, "get_int")

  def get_bool(self, name, default=None):
    return self._safe_get(name, "get_bool")

  def get_string(self, name, default=None):
    return self._safe_get(name, "get_string")
