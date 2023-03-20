#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import os


parser = argparse.ArgumentParser()
parser.add_argument("webpack_args", nargs=argparse.REMAINDER)

if __name__ == "__main__":
  args = parser.parse_args()
  os.execvp(
    "yarn",
    [
      "yarn",
      "-s",
      "webpack",
      "--config=web/js/webpack/unused_code.config.babel.js",
      *args.webpack_args,
    ],
  )
