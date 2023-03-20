# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.invite.constant import ALL_ROLES, NO_ROLE  # type: ignore
from zigopt.net.errors import BadParamError  # type: ignore


def validate_role(role: Optional[str]) -> Optional[str]:
  if role is None or role in ALL_ROLES:
    return role
  raise BadParamError(f"Invalid role: `{role}`")


def validate_invite_role(role: Optional[str]) -> Optional[str]:
  if role is None or role in ALL_ROLES and role != NO_ROLE:
    return role
  raise BadParamError(f"Invalid invite role: `{role}`")
