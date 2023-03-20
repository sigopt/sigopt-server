# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import validates

from zigopt.db.column import ImpliedUTCDateTime
from zigopt.db.declarative import Base
from zigopt.membership.model import MEMBERSHIP_TYPE_DB_ENUM
from zigopt.user.model import normalize_email


class Invite(Base):
  __tablename__ = "invites"
  __table_args__ = (
    UniqueConstraint("id", "organization_id"),
    UniqueConstraint("organization_id", "email"),
  )

  id = Column(BigInteger, primary_key=True)
  email = Column(String, index=True)
  organization_id = Column(
    BigInteger,
    ForeignKey("organizations.id", name="invites_organization_id_fkey", ondelete="CASCADE"),
    index=True,
  )
  inviter = Column(
    BigInteger,
    ForeignKey("users.id", name="invites_inviter_fkey", ondelete="CASCADE"),
    index=True,
  )
  timestamp = Column(ImpliedUTCDateTime)
  invite_code = Column(String)
  membership_type = Column(MEMBERSHIP_TYPE_DB_ENUM)

  @validates("email")
  def validate_email(self, key, email):
    assert "@" in email
    return normalize_email(email)
