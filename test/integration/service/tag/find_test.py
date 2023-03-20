# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.protobuf.gen.color.color_pb2 import Color
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.tag.model import Tag

from integration.service.tag.test_base import TagServiceTestBase


class TestTagServiceFind(TagServiceTestBase):
  def test_find_tags_by_client_id(self, services, client, another_client, tag_service):
    assert client.id != another_client.id

    client_tags = tag_service.find_by_client_id(client.id)
    assert client_tags == []
    another_client_tags = tag_service.find_by_client_id(another_client.id)
    assert another_client_tags == []

    tag_names = [f"tag{i}" for i in range(3)]
    for tag_name in tag_names:
      tag = Tag(
        name=tag_name,
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=client.id,
      )
      services.database_service.insert(tag)

    client_tags = tag_service.find_by_client_id(client.id)
    assert len(client_tags) == 3
    assert set(t.name for t in client_tags) == set(tag_names)
    assert all(t.client_id == client.id for t in client_tags)
    another_client_tags = tag_service.find_by_client_id(another_client.id)
    assert another_client_tags == []

    for tag_name in tag_names:
      tag = Tag(
        name=tag_name,
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=another_client.id,
      )
      services.database_service.insert(tag)

    client_tags = tag_service.find_by_client_id(client.id)
    assert len(client_tags) == 3
    assert set(t.name for t in client_tags) == set(tag_names)
    assert all(t.client_id == client.id for t in client_tags)
    another_client_tags = tag_service.find_by_client_id(another_client.id)
    assert len(another_client_tags) == 3
    assert set(t.name for t in another_client_tags) == set(tag_names)
    assert all(t.client_id == another_client.id for t in another_client_tags)

  def test_cant_find_tag(self, client, tag_service):
    tag = tag_service.find_by_client_and_id(client_id=client.id, tag_id=0)
    assert tag is None

  def test_cant_find_tag_in_another_client(self, services, client, another_client, tag_service):
    assert client.id != another_client.id

    tag_in_another_client = Tag(
      name="test tag",
      data=TagData(color=Color(red=1, green=2, blue=3)),
      client_id=another_client.id,
    )
    services.database_service.insert(tag_in_another_client)
    tag = tag_service.find_by_client_and_id(client_id=client.id, tag_id=tag_in_another_client.id)
    assert tag is None

  def test_find_tag_by_client_and_id(self, services, client, tag_service):
    tag = Tag(
      name="test tag",
      data=TagData(color=Color(red=1, green=2, blue=3)),
      client_id=client.id,
    )
    services.database_service.insert(tag)
    assert tag.id is not None
    found_tag = tag_service.find_by_client_and_id(client_id=client.id, tag_id=tag.id)
    assert found_tag is not None
    assert found_tag.id == tag.id
    self.assert_tags_are_equal(found_tag, tag)

  def test_count_tags_by_client_id(self, services, client, another_client, tag_service):
    assert client.id != another_client.id

    assert tag_service.count_by_client_id(client.id) == 0
    assert tag_service.count_by_client_id(another_client.id) == 0

    tag_names = [f"tag{i}" for i in range(3)]
    for tag_name in tag_names:
      tag = Tag(
        name=tag_name,
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=client.id,
      )
      services.database_service.insert(tag)

    assert tag_service.count_by_client_id(client.id) == 3
    assert tag_service.count_by_client_id(another_client.id) == 0

    for tag_name in tag_names:
      tag = Tag(
        name=tag_name,
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=another_client.id,
      )
      services.database_service.insert(tag)

    assert tag_service.count_by_client_id(client.id) == 3
    assert tag_service.count_by_client_id(another_client.id) == 3
