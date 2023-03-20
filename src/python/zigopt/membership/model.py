# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import enum

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Index

from zigopt.db.declarative import Base


class MembershipType(enum.Enum):
  member = "member"
  owner = "owner"


MEMBERSHIP_TYPE_DB_ENUM = Enum(MembershipType, name="membership_type")


class Membership(Base):
  __tablename__ = "memberships"
  __table_args__ = tuple(
    [
      Index("memberships_organization_id_idx", "organization_id"),
    ]
  )

  user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
  membership_type = Column(MEMBERSHIP_TYPE_DB_ENUM)

  def __init__(self, membership_type=None, **kwargs):
    if membership_type is None:
      membership_type = MembershipType.member
    super().__init__(membership_type=membership_type, **kwargs)

  @property
  def is_owner(self):
    return self.membership_type == MembershipType.owner
