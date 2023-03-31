#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import os


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("path", type=str)
  args = parser.parse_args()
  print(os.path.realpath(args.path))  # noqa: T001
