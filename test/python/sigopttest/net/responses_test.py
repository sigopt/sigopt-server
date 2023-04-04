# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json

import pytest

from zigopt.net.responses import dump_json


def test_dump_json_whitesapace():
  assert dump_json({}) == "{}\n"
  assert dump_json({"a": 1}) == '{\n  "a": 1\n}\n'


@pytest.mark.parametrize("char", ("<", ">", "&"))
def test_dump_json_escape(char):
  serialized = dump_json({"a": char})
  assert char not in serialized
  hexed = hex(ord(char))[-2:].upper()
  assert len(hexed) == 2
  assert f"\\u00{hexed}" in serialized


@pytest.mark.parametrize(
  "obj",
  (
    {},
    {"test": "ok"},
    {"test": 1},
    {"test": None},
    {'"><img src=x onerror=alert(document.location)>"': '"><img src=x onerror=alert(document.location)>"'},
  ),
)
def test_dump_json_consistency(obj):
  assert json.loads(dump_json(obj)) == obj
