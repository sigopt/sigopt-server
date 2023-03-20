# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.organization.organizationmeta_pb2 import OrganizationMeta


class Organization(Base):
  NAME_MAX_LENGTH = 100

  __tablename__ = "organizations"
  id = Column(BigInteger, primary_key=True)
  date_created = Column(ImpliedUTCDateTime)
  name = Column(String)
  organization_meta = ProtobufColumn(OrganizationMeta, name="organization_meta_json")
  date_deleted = Column(ImpliedUTCDateTime)

  def __init__(self, date_created=None, organization_meta=None, **kwargs):
    if date_created is None:
      date_created = current_datetime()
    if organization_meta is None:
      organization_meta = Organization.organization_meta.default_value()
    super().__init__(date_created=date_created, organization_meta=organization_meta, **kwargs)

  @validates("organization_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  @property
  def deleted(self):
    return bool(self.date_deleted)

  @property
  def academic(self):
    return self.organization_meta.academic
