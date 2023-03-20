# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import secrets
import string
from typing import Any as _Any


def is_string(val: _Any) -> bool:
  return isinstance(val, str)


def is_serial(val: _Any) -> bool:
  return isinstance(val, (str, bytes))


def is_likely_random_string(val: _Any) -> bool:
  return is_string(val) and all(c in string.ascii_uppercase for c in val)


def random_string(str_length: int = 48) -> str:
  return "".join(secrets.choice(string.ascii_uppercase) for _ in range(str_length))
