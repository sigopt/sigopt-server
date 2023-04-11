# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.membership.model import MembershipType
from zigopt.net.errors import BadParamError


def validate_membership_type(membership_type: Optional[str]) -> Optional[MembershipType]:
  if membership_type and membership_type not in MembershipType.__members__:
    raise BadParamError(
      f"Unrecognized membership type {membership_type} (if provided, must be one of {list(MembershipType.__members__)}"
    )
  return MembershipType[membership_type] if membership_type else None
