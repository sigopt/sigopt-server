# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# NOTE: these models are built around SQLAlchemy's support for single-table inheritance (STI)
# See here: https://docs.sqlalchemy.org/en/13/orm/inheritance.html#single-table-inheritance

import enum

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, ForeignKeyConstraint, Index, Text

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime
from zigopt.db.declarative import Base


class NoteType(enum.Enum):
  PROJECT = "project-note"


class Note(Base):
  __tablename__ = "notes"

  id = Column(BigInteger, primary_key=True)
  note_type = Column(
    Enum(
      NoteType,
      name="note_types",
      values_callable=lambda e: [note_type.value for note_type in e],
    ),
    nullable=False,
  )
  contents = Column(Text, nullable=False)
  created_by = Column(
    BigInteger,
    ForeignKey("users.id", name="notes_created_by_fkey", ondelete="SET NULL"),
  )
  date_created = Column(ImpliedUTCDateTime, nullable=False)

  __mapper_args__ = {"polymorphic_on": note_type}
  __table_args__ = (
    Index("ix_notes_note_type", "note_type"),
    Index("ix_notes_date_created", "date_created"),
  )

  # NOTE: forces construction via specific note type
  def __new__(cls, *args, **kwargs):
    if cls is Note:
      raise TypeError("The Note class is abstract and cannot be instantiated. Use one of its child classes instead.")
    return super().__new__(cls)

  def __init__(self, *args, **kwargs):
    kwargs.setdefault(Note.date_created.key, current_datetime())
    super().__init__(*args, **kwargs)


class ProjectNote(Note):
  project_client_id = Column(BigInteger)
  project_project_id = Column(BigInteger)

  __mapper_args__ = {"polymorphic_identity": NoteType.PROJECT}


# NOTE: these must be placed outside of the child classes of Note
# because STI makes it so that you can't have __table_args__ on them
ForeignKeyConstraint(
  [ProjectNote.project_client_id, ProjectNote.project_project_id],
  ["projects.client_id", "projects.id"],
  name="notes_project_client_id_project_project_id_fkey",
  ondelete="CASCADE",
)
Index(
  "ix_notes_project_client_id_project_project_id",
  ProjectNote.project_client_id,
  ProjectNote.project_project_id,
  postgresql_where=(ProjectNote.project_client_id.isnot(None) & ProjectNote.project_project_id.isnot(None)),
)
