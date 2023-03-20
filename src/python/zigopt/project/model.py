# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, PrimaryKeyConstraint, Sequence, String, UniqueConstraint
from sqlalchemy.orm import validates

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.project.projectdata_pb2 import ProjectData


MAX_NAME_LENGTH = 100

MAX_ID_LENGTH = 32

PROJECTS_ID_SEQ = "projects_id_seq"


class Project(Base):
  __tablename__ = "projects"

  id = Column(BigInteger, Sequence(PROJECTS_ID_SEQ), nullable=False)
  reference_id = Column(String(MAX_ID_LENGTH), nullable=False)
  client_id = Column(BigInteger, ForeignKey("clients.id"), nullable=False)
  name = Column(String(MAX_NAME_LENGTH), nullable=False)
  date_created = Column(ImpliedUTCDateTime, nullable=False)
  date_updated = Column(ImpliedUTCDateTime, nullable=False)
  deleted = Column(Boolean, default=False, nullable=False)
  created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))
  data = ProtobufColumn(ProjectData, name="data_json", nullable=False)

  __table_args__ = tuple(
    [
      PrimaryKeyConstraint("id", "client_id"),
      UniqueConstraint("client_id", "reference_id"),
    ]
  )

  def __init__(self, *, name, reference_id, client_id, created_by, **kwargs):
    kwargs.setdefault("date_created", current_datetime())
    kwargs.setdefault("date_updated", kwargs["date_created"])
    kwargs.setdefault("deleted", False)
    kwargs.setdefault("data", type(self).data.default_value())
    super().__init__(
      name=name,
      reference_id=reference_id,
      client_id=client_id,
      created_by=created_by,
      **kwargs,
    )

  @validates("data")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)
