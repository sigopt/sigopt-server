# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64
import mimetypes
import re
import string

from sqlalchemy import BigInteger, Column, ForeignKey, Index, PrimaryKeyConstraint, Sequence, String
from sqlalchemy.orm import validates

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime, ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.file.filedata_pb2 import FileData


MAX_NAME_LENGTH = 100

FILES_ID_SEQ = "files_id_seq"

# Safe Characters as defined by AWS
# https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMetadata.html#object-key-guidelines-safe-characters
PERMITTED_FILENAME_CHARS = set(
  "".join(
    [
      string.ascii_letters,
      string.digits,
      "!-_.*'()",
    ]
  )
)


def sanitize_filename(filename):
  if filename:
    return "".join(c for c in filename if c in PERMITTED_FILENAME_CHARS)
  return filename


class File(Base):
  __tablename__ = "files"

  id = Column(BigInteger, Sequence(FILES_ID_SEQ), nullable=False)
  client_id = Column(BigInteger, ForeignKey("clients.id"), nullable=False)
  name = Column(String(MAX_NAME_LENGTH))
  filename = Column(String(MAX_NAME_LENGTH))
  date_created = Column(ImpliedUTCDateTime, nullable=False)
  # NOTE: attempting to delete a row from users will intentionally fail if the user has uploaded files
  # this is to guarantee that we remove PII from S3 before deleting a user for privacy law compliance
  created_by = Column(BigInteger, ForeignKey("users.id"))
  data = ProtobufColumn(FileData, name="data_json", nullable=False)

  __table_args__ = tuple(
    [
      PrimaryKeyConstraint("id"),
      Index("ix_files_client_id_id", "client_id", "id"),
      Index("ix_files_created_by_id", "created_by", "id"),
    ]
  )

  def __init__(self, *, name, client_id, created_by, **kwargs):
    kwargs.setdefault("date_created", current_datetime())
    kwargs.setdefault("data", type(self).data.default_value())
    super().__init__(
      name=name,
      client_id=client_id,
      created_by=created_by,
      **kwargs,
    )

  @property
  def content_md5_base64(self):
    return base64.b64encode(self.data.content_md5).decode("ascii")

  @validates("data")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  def get_download_filename(self):
    if self.filename:
      name_part = sanitize_filename(re.split(r"[/\\]", self.filename)[-1])
      if name_part:
        return name_part
    basename = sanitize_filename(self.name) or str(self.id)
    overrides = {
      # mimetypes.guess_extension returns .jpe for JPEG images, .jpg is much more common
      # and .bat for text/plain, .txt is much more common
      "image/jpeg": ".jpg",
      "text/plain": ".txt",
    }
    mime_type = self.data.content_type
    if (extension := overrides.get(mime_type)) is None:
      extension = mimetypes.guess_extension(self.data.content_type)
    if extension is None:
      extension = ""
    return basename + extension
