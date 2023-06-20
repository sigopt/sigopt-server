# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKeyConstraint, Index, UniqueConstraint
from sqlalchemy.orm import validates

from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta


class Permission(Base):
  __tablename__ = "roles"
  __table_args__ = (
    Index("ix_roles_user_id", "user_id"),
    UniqueConstraint("client_id", "user_id"),
    ForeignKeyConstraint(
      ["user_id", "organization_id"],
      ["memberships.user_id", "memberships.organization_id"],
      ondelete="cascade",
    ),
    ForeignKeyConstraint(
      ["organization_id", "client_id"],
      ["clients.organization_id", "clients.id"],
      onupdate="cascade",
      ondelete="cascade",
    ),
  )

  id = Column(BigInteger, primary_key=True)
  client_id = Column(BigInteger)
  organization_id = Column(BigInteger)
  user_id = Column(BigInteger)
  permission_meta: PermissionMeta = ProtobufColumn(
    PermissionMeta,
    proxy=PermissionMeta,
    name="permission_meta_json",
    nullable=False,
  )

  def __init__(self, user_id, client_id, organization_id, permission_meta=None, **kwargs):
    if permission_meta is None:
      permission_meta = PermissionMeta()
    super().__init__(
      user_id=user_id, client_id=client_id, organization_id=organization_id, permission_meta=permission_meta, **kwargs
    )

  @validates("permission_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=PermissionMeta)

  @property
  def can_admin(self):
    return self.permission_meta.can_admin

  @property
  def can_write(self):
    return self.permission_meta.can_write

  @property
  def can_read(self):
    return self.permission_meta.can_read

  @property
  def can_see_experiments_by_others(self):
    return self.permission_meta.can_see_experiments_by_others
