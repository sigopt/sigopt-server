# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.protobuf.gen.color.color_pb2 import Color
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.tag.model import Tag

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestCreateTags(V1Base):
  @classmethod
  def get_tag_count(cls, services, client_id):
    return services.tag_service.count_by_client_id(client_id)

  def test_tag_create(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test tag create"
    tag_color = "#123456"
    tag = (
      connection.clients(connection.client_id)
      .tags()
      .create(
        name=tag_name,
        color=tag_color,
      )
    )
    assert tag.id is not None
    assert tag.color == tag_color
    assert tag.name == tag_name
    tag_object = services.tag_service.find_by_client_and_id(client_id=connection.client_id, tag_id=tag.id)
    assert tag_object.name == tag_name
    assert tag_object.data.color.red == 0x12
    assert tag_object.data.color.green == 0x34
    assert tag_object.data.color.blue == 0x56
    assert self.get_tag_count(services, connection.client_id) == 1

  def test_tag_create_fails_without_name(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_color = "#123456"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).tags().create(
        color=tag_color,
      )
    assert self.get_tag_count(services, connection.client_id) == 0

  def test_tag_create_fails_with_blank_name(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_color = "#123456"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).tags().create(
        name="",
        color=tag_color,
      )
    assert self.get_tag_count(services, connection.client_id) == 0

  def test_tag_create_fails_without_color(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test no color"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).tags().create(
        name=tag_name,
      )
    assert self.get_tag_count(services, connection.client_id) == 0

  def test_tag_create_fails_with_extra_keys(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test no color"
    tag_color = "#123456"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).tags().create(
        name=tag_name,
        color=tag_color,
        key_that_will_never_be_used=True,
      )
    assert self.get_tag_count(services, connection.client_id) == 0

  def test_tag_create_fails_with_conflicting_name(self, services, connection):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test tag create"
    tag_color = "#123456"
    services.tag_service.insert(
      Tag(
        name=tag_name,
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=connection.client_id,
      )
    )
    with RaisesApiException(HTTPStatus.CONFLICT):
      connection.clients(connection.client_id).tags().create(
        name=tag_name,
        color=tag_color,
      )
    assert self.get_tag_count(services, connection.client_id) == 1

  @pytest.mark.parametrize(
    "color",
    [
      "#000000",
      "#999999",
      "#aaaaaa",
      "#ffffff",
      "#AAAAAA",
      "#FFFFFF",
      "#1a2b3c",
      "#1A2B3C",
    ],
  )
  def test_tag_create_valid_colors(self, services, connection, color):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test tag create"
    tag_color = color
    tag = (
      connection.clients(connection.client_id)
      .tags()
      .create(
        name=tag_name,
        color=tag_color,
      )
    )
    assert tag.color == color.upper()
    assert self.get_tag_count(services, connection.client_id) == 1

  @pytest.mark.parametrize(
    "color",
    [
      "",
      " ",
      "hello",
      "red",
      "#a",
      "#A",
      "#123",
      "#abc",
      "#EGBDFA",
      "#-12885",
    ],
  )
  def test_tag_create_invalid_colors(self, services, connection, color):
    assert self.get_tag_count(services, connection.client_id) == 0
    tag_name = "test tag create"
    tag_color = color
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).tags().create(
        name=tag_name,
        color=tag_color,
      )
    assert self.get_tag_count(services, connection.client_id) == 0
