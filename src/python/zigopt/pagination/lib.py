# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from enum import Enum

from google.protobuf.descriptor import FieldDescriptor

from zigopt.common.sigopt_datetime import naive_datetime_to_aware_datetime
from zigopt.common.struct import ImmutableStruct
from zigopt.protobuf.gen.api.paging_pb2 import PagingSymbol
from zigopt.protobuf.lib import get_oneof_value


class FieldApiType(Enum):
  id = 1
  timestamp = 2
  numeric = 3
  string = 4
  object = 5
  unknown = 6
  boolean = 7


FIELD_API_TYPE_TO_STRING = {
  FieldApiType.id: "id",
  FieldApiType.timestamp: "timestamp",
  FieldApiType.numeric: "numeric",
  FieldApiType.string: "string",
  FieldApiType.object: "object",
  FieldApiType.unknown: "unknown",
  FieldApiType.boolean: "boolean",
}

PROTOBUF_FIELD_TYPE_TO_FIELD_API_TYPE = {
  FieldDescriptor.TYPE_DOUBLE: FieldApiType.numeric,
  FieldDescriptor.TYPE_STRING: FieldApiType.string,
}

DefinedField = ImmutableStruct(
  "DefinedField",
  [
    "api_type",
    "field_count",
    "key",
    "name",
    "sortable",
  ],
)


def get_value_of_paging_symbol(symbol):
  assert isinstance(symbol, PagingSymbol)
  if symbol.WhichOneof("type") == "null_value":
    return None
  if symbol.WhichOneof("type") == "timestamp_value":
    return naive_datetime_to_aware_datetime(symbol.timestamp_value.ToDatetime())
  return get_oneof_value(symbol, "type")
