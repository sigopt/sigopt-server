# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0


def user_input_to_bool(i: str | int | bool | list | dict | None) -> bool:
  if i in ("True", "true", True):
    return True
  if i in ("False", "false", False):
    return False
  raise ValueError(f"{i} is not a valid boolean")


def maybe_decode(value: bytes | str) -> str:
  if isinstance(value, bytes):
    return value.decode("utf-8")
  return value
