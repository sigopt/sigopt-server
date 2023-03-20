# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os


def ensure_dir(path):
  try:
    os.makedirs(path)
  except OSError:
    pass
