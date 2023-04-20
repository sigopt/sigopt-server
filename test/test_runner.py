#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import sys
import warnings

import pytest
from sigopt_config.broker import ConfigBroker

from zigopt.config import DEFAULT_CONFIG_DIR
from zigopt.log.base import base_logger_setup, configure_loggers


if __name__ == "__main__":
  base_logger_setup()
  warnings.simplefilter("error", append=True)

  parser = argparse.ArgumentParser()
  parser.add_argument("--config-dir", type=str, default=DEFAULT_CONFIG_DIR)
  parser.add_argument("--ssh-args", type=str, default="")
  parser.add_argument("--test-target-name", type=str, default=None)
  parser.add_argument("suite", nargs="?", default="test/integration")
  args, unknown_args = parser.parse_known_args()

  config_broker = ConfigBroker.from_directory(args.config_dir)
  configure_loggers(config_broker)

  pytest_args = list(unknown_args)

  pytest_args.extend(
    [
      "-rwq",
      "--strict-markers",
      "--durations",
      "5",
      "--config-dir",
      args.config_dir,
      args.suite,
    ]
  )

  sys.exit(pytest.main(pytest_args))
