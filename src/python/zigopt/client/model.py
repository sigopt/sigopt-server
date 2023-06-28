# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta


class Client(Base):
  NAME_MAX_LENGTH = 100

  __tablename__ = "clients"
  __table_args__ = tuple(
    [
      UniqueConstraint("organization_id", "id"),
    ]
  )

  id = Column(BigInteger, primary_key=True)
  name = Column(String)
  client_meta: ClientMeta = ProtobufColumn(ClientMeta, name="client_meta_json")
  organization_id = Column(BigInteger, ForeignKey("organizations.id"), nullable=False)

  def __init__(self, organization_id, client_meta=None, **kwargs):
    if client_meta is None:
      client_meta = ClientMeta()
    super().__init__(organization_id=organization_id, client_meta=client_meta, **kwargs)

  @validates("client_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  @property
  def date_created(self):
    return self.client_meta.date_created

  @property
  def deleted(self):
    return self.client_meta.deleted

  @property
  def client_security(self):
    return self.client_meta.client_security

  @property
  def allow_users_to_see_experiments_by_others(self):
    return self.client_security.allow_users_to_see_experiments_by_others
