# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

from sigopt_config.broker import ConfigBroker


DEFAULT_CONFIG_DIR = "/etc/sigopt/server-config/"


def load_config_from_env() -> ConfigBroker:
  config_dir = os.environ.get("SIGOPT_SERVER_CONFIG_DIR") or DEFAULT_CONFIG_DIR
  print(os.environ.get("SIGOPT_SERVER_CONFIG_DIR"), config_dir)
  print(os.environ)
  return ConfigBroker.from_directory(config_dir)
