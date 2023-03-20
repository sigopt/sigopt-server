# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import to_map_by_key
from zigopt.protobuf.gen.color.color_pb2 import Color
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.tag.model import Tag

from integration.v1.test_base import V1Base


class TestListTags(V1Base):
  @classmethod
  def get_tag_count(cls, services, client_id):
    return services.tag_service.count_by_client_id(client_id)

  def test_list_no_tags(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0

    tags = list(connection.clients(connection.client_id).tags().fetch().iterate_pages())
    assert tags == []

  def test_list_tags(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0

    tag_names = [f"tag{i}" for i in range(3)]
    for i, tag_name in enumerate(tag_names):
      services.tag_service.insert(
        Tag(
          name=tag_name,
          data=TagData(color=Color(red=i, green=i, blue=i)),
          client_id=connection.client_id,
        )
      )

    tags = list(connection.clients(connection.client_id).tags().fetch().iterate_pages())
    assert len(tags) == 3
    assert set(t.name for t in tags) == set(tag_names)
    assert all(t.client == str(connection.client_id) for t in tags)
    tags_by_name = to_map_by_key(tags, lambda t: t.name)
    for i, tag_name in enumerate(tag_names):
      assert tags_by_name[tag_name].color == "#" + f"{i:02X}" * 3
