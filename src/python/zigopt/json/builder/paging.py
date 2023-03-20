# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Optional, Sequence

from zigopt.common import *
from zigopt.api.paging import serialize_paging_marker  # type: ignore
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.pagination.lib import FIELD_API_TYPE_TO_STRING, DefinedField  # type: ignore
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker  # type: ignore


class DefinedFieldJsonBuilder(JsonBuilder):
  object_name = "field"

  def __init__(self, defined_field: DefinedField):
    self._defined_field = defined_field

  @field(ValidationType.integer)
  def count(self) -> int:
    return self._defined_field.field_count

  @field(ValidationType.string)
  def key(self) -> str:
    return self._defined_field.key

  @field(ValidationType.string)
  def name(self) -> str:
    return self._defined_field.name

  @field(ValidationType.boolean)
  def sortable(self) -> bool:
    return self._defined_field.sortable

  @field(ValidationType.string)
  def type(self) -> str:
    return FIELD_API_TYPE_TO_STRING[self._defined_field.api_type]


class PaginationJsonBuilder(JsonBuilder):
  object_name = "pagination"

  def __init__(
    self,
    data: Optional[Sequence[JsonBuilder]] = None,
    count: Optional[int] = None,
    before: Optional[PagingMarker] = None,
    after: Optional[PagingMarker] = None,
    defined_fields: Optional[Sequence[DefinedField]] = None,
  ):
    self._data = data or []
    self._count = count
    self._before = before
    self._after = after
    self._fields: Optional[Sequence[str]] = None
    self._defined_fields = defined_fields

  def resolve_fields(self, fields: Optional[Sequence[str]] = None) -> dict[str, Any]:
    self._fields = fields
    json = super().resolve_fields(fields=None)
    self._fields = None
    return json

  @field(ValidationType.object)
  def paging(self) -> dict[str, Optional[str]]:
    return dict(
      after=napply(self._after, serialize_paging_marker),
      before=napply(self._before, serialize_paging_marker),
    )

  @field(ValidationType.integer)
  def count(self) -> Optional[int]:
    return coalesce(self._count, len(self._data))

  @field(ValidationType.arrayOf(ValidationType.object))
  def data(self) -> list[dict[str, Any]]:
    return [d.resolve_fields(self._fields) for d in self._data]

  def hide_defined_fields(self):
    return self._defined_fields is None

  @field(ValidationType.arrayOf(JsonBuilderValidationType()), hide=hide_defined_fields)
  def defined_fields(self) -> list[DefinedFieldJsonBuilder]:
    return [DefinedFieldJsonBuilder(df) for df in (self._defined_fields or [])]
