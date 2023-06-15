# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import TypeVar


T = TypeVar("T")

__all__ = ["maybe_decode"]


def maybe_decode(value: bytes | T) -> str | T:
  if isinstance(value, bytes):
    return value.decode("utf-8")
  return value
