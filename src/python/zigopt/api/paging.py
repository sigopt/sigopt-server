# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import base64
import binascii

from google.protobuf.message import DecodeError

from zigopt.common import *
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker


def decode_base64_marker_without_padding(serialized_marker):
  # NOTE: "=" padding needs to be added to the marker in order for it to be correctly decoded
  if tail_len := len(serialized_marker) % 4:
    serialized_marker += "=" * (4 - tail_len)
  return base64.urlsafe_b64decode(serialized_marker)


def encode_base64_marker_without_padding(marker):
  # NOTE: "=" padding needs to be stripped since it is not url safe
  return base64.urlsafe_b64encode(marker).decode("utf-8").replace("=", "")


def deserialize_paging_marker(serialized_marker):
  if serialized_marker == "":
    raise BadParamError("Invalid paging marker, cannot be an empty string")
  marker = PagingMarker()
  try:
    marker.ParseFromString(decode_base64_marker_without_padding(serialized_marker))
  except (DecodeError, binascii.Error, SystemError) as e:
    raise BadParamError(f"Invalid paging marker: {serialized_marker}") from e
  return marker


def serialize_paging_marker(marker):
  serialized_marker = encode_base64_marker_without_padding(marker.SerializeToString())
  assert serialized_marker
  return serialized_marker
