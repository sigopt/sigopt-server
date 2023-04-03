# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
from typing import Any, Optional

from google.protobuf.struct_pb2 import Struct  # pylint: disable=no-name-in-module

from zigopt.common import *
from zigopt.api.validate_schema import validate
from zigopt.experiment.model import Experiment  # type: ignore
from zigopt.net.errors import BadParamError  # type: ignore
from zigopt.protobuf.dict import dict_to_protobuf_struct, is_protobuf_struct, protobuf_struct_to_dict  # type: ignore


def _schema_validate(metadata: dict[str, Any], length: int, key_length: int, max_keys: int) -> None:
  validate(
    metadata,
    {
      "type": "object",
      "maxProperties": max_keys,
      "additionalProperties": {
        "type": ["string", "number", "null"],
        "minLength": 0,
        "maxLength": length,
      },
    },
  )
  for key in metadata:
    if len(key) > key_length:
      key_str = f"{key[:10]}...{key[-10:]}" if len(key) > 20 else key
      raise BadParamError(f"The length of the metadata key '{key_str}' must be less than {key_length}")


def validate_custom_json(metadata: dict[str, Any]) -> Optional[str]:
  if metadata is not None:
    return json.dumps(remove_nones(metadata))
  return None


def validate_metadata(
  metadata: Struct,
  length: int = Experiment.CLIENT_PROVIDED_DATA_MAX_LENGTH,
  key_length: int = Experiment.CLIENT_PROVIDED_DATA_MAX_KEY_LENGTH,
  max_keys: int = Experiment.CLIENT_PROVIDED_DATA_MAX_KEYS,
) -> Struct:
  assert metadata is not None
  assert is_protobuf_struct(metadata)

  # TODO(SN-1104): Some of this validation could be perhaps done in ValidationType.metadata, but
  # wanted to have it in the same place as validate_client_provided_data to ensure consistency
  as_dict = protobuf_struct_to_dict(metadata)
  _schema_validate(as_dict, length=length, key_length=key_length, max_keys=max_keys)
  as_dict_no_none: dict[str, Any] = remove_nones_mapping(as_dict)
  metadata_s = dict_to_protobuf_struct(as_dict_no_none)

  return metadata_s


def validate_client_provided_data(
  metadata: dict[str, Any],
  length: int = Experiment.CLIENT_PROVIDED_DATA_MAX_LENGTH,
  key_length: int = Experiment.CLIENT_PROVIDED_DATA_MAX_KEY_LENGTH,
  max_keys: int = Experiment.CLIENT_PROVIDED_DATA_MAX_KEYS,
) -> Optional[str]:
  if metadata is not None:
    _schema_validate(metadata, length=length, key_length=key_length, max_keys=max_keys)
    return validate_custom_json(metadata)
  return None
