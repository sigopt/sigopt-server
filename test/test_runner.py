#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import sys
import warnings

import pytest

from zigopt.config.broker import ConfigBroker
from zigopt.log.base import base_logger_setup, configure_loggers


if __name__ == "__main__":
  base_logger_setup()
  warnings.simplefilter("error", append=True)

  parser = argparse.ArgumentParser()
  parser.add_argument("--config-file", type=str, default="config/development.json")
  parser.add_argument("--ssh-args", type=str, default="")
  parser.add_argument("--test-target-name", type=str, default=None)
  parser.add_argument("suite", nargs="?", default="test/integration")
  args, unknown_args = parser.parse_known_args()

  config_broker = ConfigBroker.from_file(args.config_file)
  configure_loggers(config_broker)
  if config_broker.get("smtp.test_launch", True):
    config_broker["smtp.host"] = None
  config_broker["db.host"] = config_broker.get("db.test_host", config_broker.get("db.host"))
  config_broker["db.port"] = config_broker.get("db.test_port", config_broker.get("db.port"))
  config_broker["redis.host"] = config_broker.get("redis.test_host", config_broker.get("redis.host"))
  config_broker["redis.port"] = config_broker.get("redis.test_port", config_broker.get("redis.port"))
  if args.test_target_name:
    config_broker["test_target_name"] = args.test_target_name

  pytest_args = list(unknown_args)

  pytest_args.extend(
    [
      "-rwq",
      "--strict-markers",
      "--durations",
      "5",
      "--config-file",
      args.config_file,
      args.suite,
    ]
  )

  sys.exit(pytest.main(pytest_args))
