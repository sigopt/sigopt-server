# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, expose_fields, field
from zigopt.tag.model import Tag


class TagJsonBuilder(JsonBuilder):
  object_name = "tag"

  def __init__(self, tag: Tag):
    self._tag = tag

  @expose_fields(
    fields=[
      ("id", ValidationType.id),
      ("name", ValidationType.string),
    ]
  )
  def expose_tag(self) -> Tag:
    return self._tag

  @field(ValidationType.color_hex)
  def color(self) -> int:
    return self._tag.data.color

  @field(ValidationType.id)
  def client(self) -> int:
    return self._tag.client_id
