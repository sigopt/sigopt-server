# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os


def is_candidate(candidate):
  basename = os.path.basename(candidate)
  is_executable = os.path.isfile(candidate) and os.access(candidate, os.X_OK)
  is_sh_file = basename.endswith(".sh")
  if is_executable or is_sh_file:
    if is_sh_file or "." not in basename:
      return True
  return False
