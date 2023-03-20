# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.protobuf.gen.color.color_pb2 import Color
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.tag.model import Tag
from zigopt.tag.service import TagExistsException

from integration.service.tag.test_base import TagServiceTestBase


class TestTagServiceInsert(TagServiceTestBase):
  def test_insert_tag(self, services, client, tag_service):
    tag_data = TagData(color=Color(red=0x77, green=0x77, blue=0x77))
    tag = Tag(name="test tag", data=tag_data, client_id=client.id)
    inserted_tag = tag_service.insert(tag)
    assert inserted_tag.id is not None
    self.assert_tags_are_equal(inserted_tag, tag)

  def test_insert_conflicting_tags(self, services, client, tag_service):
    tag_data = TagData(color=Color(red=0x77, green=0x77, blue=0x77))
    tag_success, tag_fail = (Tag(name="test tag", data=tag_data, client_id=client.id) for _ in range(2))
    tag_service.insert(tag_success)
    with pytest.raises(TagExistsException):
      tag_service.insert(tag_fail)

  def test_in_different_clients_with_same_name(self, services, client, another_client, tag_service):
    tag_data = TagData(color=Color(red=0x77, green=0x77, blue=0x77))
    tag, another_tag = (Tag(name="test tag", data=tag_data, client_id=c.id) for c in (client, another_client))
    tag1 = tag_service.insert(tag)
    tag2 = tag_service.insert(another_tag)
    assert tag1.id != tag2.id
