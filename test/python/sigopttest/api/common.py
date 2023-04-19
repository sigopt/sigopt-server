# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-

import json

import pytest

from zigopt.api import request
from zigopt.api.request import InvalidJsonValue

from libsigopt.aux.errors import InvalidKeyError, SigoptValidationError


class TestJsonHandling:

  """Test json loading (i.e., from client requests) handles duplicates correctly."""

  def test_object_pairs_hook_raise_on_duplicates(self):
    no_dupes = [("hi", 2), (1.2, 3.1), (11, "bye")]
    dupes = no_dupes + [("hi", 3)]

    assert request.object_pairs_hook_raise_on_duplicates(no_dupes) == dict(no_dupes)

    with pytest.raises(InvalidKeyError):
      request.object_pairs_hook_raise_on_duplicates(dupes)

  def test_overflow_json_value(self):
    with pytest.raises(InvalidJsonValue):
      request.as_json('{"a":1e+400}'.encode())

  def test_as_json(self):
    no_dupes_str = '{"hi": 2, "1.2": 3.1, "11": "bye"}'
    no_dupes_json = json.loads(no_dupes_str)

    assert request.as_json(no_dupes_str.encode()) == no_dupes_json
    assert no_dupes_json["hi"] == 2
    assert no_dupes_json["1.2"] == 3.1
    assert no_dupes_json["11"] == "bye"

    dupes_str = no_dupes_str[0:-1] + ', "hi": 3}'
    dupes_json = json.loads(dupes_str)
    assert dupes_json["hi"] == 3

    with pytest.raises(InvalidKeyError):
      request.as_json(dupes_str.encode())

    bad_str = b"{"
    with pytest.raises(SigoptValidationError):
      request.as_json(bad_str)

  def test_unicode(self):
    unicode_key = "test 👑  key"
    unicode_value = "test 👑  value"
    unicode_string = f'{{"{unicode_key}":"{unicode_value}"}}'

    assert request.as_json(unicode_string.encode("utf-8"), encoding="utf-8") == {unicode_key: unicode_value}
