# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.note.model import Note
from zigopt.project.model import Project


class BaseNoteJsonBuilder(JsonBuilder):
  def __init__(self, note: Note):
    self._note = note

  @field(ValidationType.string)
  def contents(self) -> str:
    return self._note.contents

  @field(ValidationType.integer)
  def created(self) -> float:
    return datetime_to_seconds(self._note.date_created)

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._note.created_by


class ProjectNoteJsonBuilder(BaseNoteJsonBuilder):
  object_name = "project_note"

  def __init__(self, note: Note, project: Project):
    super().__init__(note)
    self._project = project

  @field(ValidationType.id)
  def client(self) -> int:
    return self._note.project_client_id

  @field(ValidationType.id_string)
  def project(self) -> str:
    return self._project.reference_id
