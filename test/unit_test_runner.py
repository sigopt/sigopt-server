#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import sys
import warnings

import pytest

from zigopt.log.base import base_logger_setup


if __name__ == "__main__":
  base_logger_setup()
  warnings.simplefilter("error", append=True)

  parser = argparse.ArgumentParser()
  parser.add_argument("pytest_dir", type=str, default="./test/python/sigopttest", nargs="?")
  args, unknown_args = parser.parse_known_args()

  pytest_args = [
    args.pytest_dir,
    "-rwq",
    "--strict-markers",
    "--durations",
    "5",
  ]
  pytest_args.extend(unknown_args)

  sys.exit(pytest.main(pytest_args))
