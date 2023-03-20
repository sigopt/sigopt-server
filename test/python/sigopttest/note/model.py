# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.note.model import Note, NoteType, ProjectNote


class TestNote(object):
  def assert_base_attrs(self, note):
    assert note.contents is None
    assert note.created_by is None
    assert bool(note.date_created)

  def test_cannot_create_abstract_note_object(self):
    with pytest.raises(TypeError):
      Note()

  def test_project_note(self):
    note = ProjectNote()

    self.assert_base_attrs(note)
    assert note.note_type == NoteType.PROJECT
    assert note.project_client_id is None
    assert note.project_project_id is None
