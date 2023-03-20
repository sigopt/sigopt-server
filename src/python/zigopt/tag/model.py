# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKey, PrimaryKeyConstraint, Sequence, String, UniqueConstraint
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData


class Tag(Base):
  NAME_MAX_LENGTH = 100
  TAG_ID_SEQ = "tag_id_seq"
  PRIMARY_KEY_INDEX_NAME = "tags_id_client_id_pkey"
  UNIQUE_NAME_INDEX_NAME = "tags_client_id_name_key"

  __tablename__ = "tags"

  id = Column(BigInteger, Sequence(TAG_ID_SEQ), nullable=False)
  name = Column(String(NAME_MAX_LENGTH), nullable=False)
  client_id = Column(BigInteger, ForeignKey("clients.id"), nullable=False)
  data = ProtobufColumn(TagData, name="data_json")

  __table_args__ = tuple(
    [
      PrimaryKeyConstraint(
        "id",
        "client_id",
        name=PRIMARY_KEY_INDEX_NAME,
      ),
      UniqueConstraint(
        "client_id",
        "name",
        name=UNIQUE_NAME_INDEX_NAME,
      ),
    ]
  )

  def __init__(self, data=None, **kwargs):
    if data is None:
      data = Tag.data.default_value()
    super().__init__(data=data, **kwargs)

  @validates("data")
  def validator(self, key, data):
    return ProtobufColumnValidator(data)
