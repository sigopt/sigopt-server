# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from html5_parser import parse


def validate_html(text):
  tree = parse(text.encode("utf-8"))
  assert tree is not None
  return tree
