# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0


def maybe_decode(value: bytes | str) -> str:
  if isinstance(value, bytes):
    return value.decode("utf-8")
  return value
