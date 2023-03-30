#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import os
from test.lint.bash import is_candidate as is_sh_candidate

from tools.lint.bash.custom_lint import custom_bash_lint


def run_bash_lint(filename):
  shellcheck = subprocess.call(["shellcheck", filename, "--exclude", "SC1090,SC1091,SC2029", "-f", "gcc"])
  custom_lint = custom_bash_lint(filename)
  if custom_lint:
    print(custom_lint)
  return any([shellcheck, custom_lint])


if __name__ == "__main__":
  import argparse
  import subprocess
  import sys

  parser = argparse.ArgumentParser()
  parser.add_argument("files", nargs="*")
  args = parser.parse_args()
  files = args.files
  if subprocess.call(["which", "shellcheck"], stdout=open(os.devnull, "w")) != 0:
    print("Install shellcheck with `brew install shellcheck`")
    sys.exit(1)
  if not files:
    files = subprocess.check_output(["git", "ls-files"]).decode("utf-8").split("\n")
  issues = [
    *(run_bash_lint(candidate) for candidate in files if is_sh_candidate(candidate)),
  ]
  sys.exit(any(issues))
