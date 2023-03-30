#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import sys


required_directives = [
  ("set -e", ("set +e", "# no_set_e")),
  ("set -o pipefail", ("set +o pipefail", "# no_pipefail")),
  # TODO(SN-1144): #! line needs to be on first line, but this isn't enforced as part of the linter
  ("#!/usr/bin/env bash", ()),
]


def custom_bash_lint(filename):
  with open(filename, "r") as f:
    lines = f.readlines()
  for directive, alternatives in required_directives:
    for line in lines:
      line = line.strip()
      if line == directive or line in alternatives:
        break
    else:
      return f"{filename}:1:1: error: Missing `{directive}` directive."
  return None


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("files", type=str, nargs="+", help="File to lint")
  args = parser.parse_args()
  responses = []
  for path in args.files:
    response = custom_bash_lint(path)
    if response:
      responses.append(response)
  if responses:
    print("\n".join(responses))  # noqa: T001
    sys.exit(1)
