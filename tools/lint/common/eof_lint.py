#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from mimetypes import guess_type
from test.lint.bash import is_candidate as is_bash_candidate

from zigopt.common.lists import generator_to_safe_iterator


SOURCES_DENY_LIST = set(
  [
    "web/static/html/google325494753540429c.html",
    "web/static/html/googlee59904019409cd29.html",
  ]
)

FILE_EXT_ALLOW_LIST = set(
  [
    ".cfg",
    ".conf",
    ".cron",
    ".csv",
    ".env",
    ".gen",
    ".hcl",
    ".html",
    ".ini",
    ".js",
    ".less",
    ".md",
    ".php",
    ".proto",
    ".py",
    ".rb",
    ".secrets",
    ".service",
    ".sh",
    ".tf",
    ".txt",
    ".yaml",
    ".yml",
  ]
)

FILE_TYPE_ALLOW_LIST = set(
  [
    "application/x-sh",
  ]
)

NONE_TYPE_FILE_ALLOW_LIST = set(
  [
    "Dockerfile",
    "Makefile",
  ]
)


class BaseRule(object):
  def verify(self, filename):
    return ""


class EndOfFileNewlineRule(BaseRule):
  def get_file_size_code(self, filename):
    with open(filename, "rb") as source_file:
      source_file.seek(0, 0)
      first_char = source_file.read(1)
      if not first_char:
        return 0
      source_file.seek(1, 0)
      second_char = source_file.read(1)
      if not second_char:
        return 1
      return 2

  def valid(self, filename):
    if self.get_file_size_code(filename) == 2:
      with open(filename, "rb") as source_file:
        source_file.seek(-1, 2)
        last_char = source_file.read(1)
        source_file.seek(-2, 2)
        second_last_char = source_file.read(1)
        return last_char == b"\n" and second_last_char != b"\n"
    return True

  def verify(self, filename):
    if self.valid(filename):
      return ""
    return r"have exactly one \n at end of file"


def prepare_all_rules(filename):
  rules = [EndOfFileNewlineRule()]
  return rules


def can_lint(source_name):
  file_type, _ = guess_type(source_name)
  file_path_prefix, file_extension = os.path.splitext(source_name)
  file_name_prefix = file_path_prefix.split("/")[-1]
  if is_bash_candidate(source_name):
    return True
  if source_name in SOURCES_DENY_LIST:
    return False
  if not file_type:
    return file_name_prefix in NONE_TYPE_FILE_ALLOW_LIST
  return file_extension in FILE_EXT_ALLOW_LIST or file_type in FILE_TYPE_ALLOW_LIST


@generator_to_safe_iterator
def check_file(source_name):
  rules = prepare_all_rules(source_name)
  for message in sorted(rule.verify(source_name) for rule in rules):
    if message:
      yield f"{source_name}: {message}"


if __name__ == "__main__":
  import os
  import subprocess
  import sys

  source_names = (e for e in subprocess.check_output(["git", "ls-files"]).decode("utf-8").split("\n") if len(e))
  source_names = [s for s in source_names if can_lint(s)]
  problems = False
  for source_name in source_names:
    for message in check_file(source_name):
      problems = True
      print(message)
  sys.exit(int(problems))
