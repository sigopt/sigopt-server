# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.struct import ImmutableStruct


Session = ImmutableStruct(
  "Session",
  [
    "api_token",
    "client",
    "code",
    "needs_password_reset",
    "user",
  ],
)
