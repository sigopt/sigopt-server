# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import subprocess  # nosec


def _run_git_command(command, path="."):
  return subprocess.check_output(command, cwd=path).decode("utf-8")


def get_git_hash(path="."):
  return git_rev_parse("HEAD", path)


def git_rev_parse(obj, path="."):
  return _run_git_command(["git", "rev-parse", obj], path).strip()
