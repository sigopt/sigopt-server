# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import ImpliedUTCDateTime
from zigopt.db.declarative import Base
from zigopt.project.model import MAX_ID_LENGTH


# Source of truth for what parent resources and web data types exist
# Add something here and you will get errors thrown everywhere you need to add something when starting api
# if you add a new parent resource - you'll have to add relevant fks to the table
web_data_types_by_resource = {"project": {"run_view": None, "ag_run_view": None}}

MAX_DISPLAY_NAME_LENGTH = 100


class WebData(Base):
  __tablename__ = "web_data"

  id = Column(BigInteger, name="id", primary_key=True)
  created = Column(ImpliedUTCDateTime, name="created", nullable=False)
  updated = Column(ImpliedUTCDateTime, name="updated", nullable=False)

  created_by = Column(
    BigInteger,
    ForeignKey("users.id", name="web_data_users_id_fk", ondelete="SET NULL"),
    name="created_by",
  )

  deleted = Column(Boolean, name="deleted", default=False, nullable=False)
  display_name = Column(Text, name="display_name")

  # What is it and what resource does it belong to?
  web_data_type = Column(Text, nullable=False)
  parent_resource_type = Column(Text, nullable=False)

  # Foreign Keys For Projects
  project_reference_id = Column(String(MAX_ID_LENGTH), nullable=False)
  project_client_id = Column(BigInteger, nullable=False)

  # Actual Information
  payload = Column(JSONB, name="payload", nullable=False)

  __table_args__ = (
    ForeignKeyConstraint(
      ["project_client_id", "project_reference_id"],
      ["projects.client_id", "projects.reference_id"],
      ondelete="CASCADE",
      name="projects_fkey",
    ),
    Index("project_client_id", "project_reference_id", "web_data_type"),
  )

  def __init__(self, *, parent_resource_type, web_data_type, parent_resource_id, display_name, **kwargs):
    kwargs.setdefault(WebData.created.key, current_datetime())
    kwargs.setdefault(WebData.updated.key, kwargs[WebData.created.key])
    assert len(display_name) <= MAX_DISPLAY_NAME_LENGTH, f"Maximum display_name length is {MAX_DISPLAY_NAME_LENGTH}"

    # Extra last minute sanity check were getting something we expect.
    project_string = "project"
    if project_string in web_data_types_by_resource and parent_resource_type == project_string:
      assert (
        web_data_types_by_resource[project_string].get(web_data_type, object()) is None
      ), f"Unrecognized web_data_type: {web_data_type}"

      super().__init__(
        display_name=display_name,
        project_reference_id=parent_resource_id["project"],
        project_client_id=int(parent_resource_id["client"]),
        parent_resource_type=parent_resource_type,
        web_data_type=web_data_type,
        **kwargs,
      )

    else:
      raise TypeError(f"Unrecognized parent_resource_type: {parent_resource_type}")
