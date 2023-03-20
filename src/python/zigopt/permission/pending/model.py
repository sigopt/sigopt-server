# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, Enum, ForeignKeyConstraint, UniqueConstraint

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime
from zigopt.db.declarative import Base
from zigopt.invite.constant import ALL_ROLES


INVITE_ROLE_DB_ENUM = Enum(*ALL_ROLES, name="role")


class PendingPermission(Base):
  __tablename__ = "pending_permissions"
  __table_args__ = (
    UniqueConstraint("invite_id", "client_id"),
    ForeignKeyConstraint(
      ["invite_id", "organization_id"],
      ["invites.id", "invites.organization_id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    ForeignKeyConstraint(["client_id", "organization_id"], ["clients.id", "clients.organization_id"]),
  )

  id = Column(BigInteger, primary_key=True)
  date_created = Column(ImpliedUTCDateTime)
  invite_id = Column(BigInteger)
  client_id = Column(BigInteger)
  organization_id = Column(BigInteger)
  role = Column(INVITE_ROLE_DB_ENUM)

  def __init__(self, invite_id, client_id, organization_id, *args, **kwargs):
    super().__init__(
      invite_id=invite_id,
      client_id=client_id,
      organization_id=organization_id,
      date_created=current_datetime(),
      *args,
      **kwargs
    )
