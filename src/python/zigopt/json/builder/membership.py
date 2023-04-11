# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.organization import OrganizationJsonBuilder
from zigopt.json.builder.user import UserJsonBuilder
from zigopt.membership.model import Membership, MembershipType
from zigopt.organization.model import Organization
from zigopt.user.model import User


class MembershipJsonBuilder(JsonBuilder):
  object_name = "membership"

  def __init__(self, membership: Membership, organization: Organization, user: User):
    self._membership = membership
    self._organization = organization
    self._user = user

  @field(JsonBuilderValidationType())
  def organization(self) -> Optional[OrganizationJsonBuilder]:
    if self._organization is not None:
      return OrganizationJsonBuilder(self._organization)
    return None

  @field(ValidationType.enum(MembershipType))
  def type(self) -> Optional[str]:
    membership_type: MembershipType = self._membership.membership_type
    return napply(membership_type, lambda t: t.value)

  @field(JsonBuilderValidationType())
  def user(self) -> Optional[UserJsonBuilder]:
    return napply(self._user, UserJsonBuilder)
