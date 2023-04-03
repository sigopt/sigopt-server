# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import json
import re
from collections.abc import Mapping
from numbers import Integral

from jsonschema import validate as validate_against_schema  # type: ignore
from jsonschema.exceptions import ValidationError  # type: ignore

from zigopt.api.errors import (
  InvalidKeyError,
  InvalidTypeError,
  InvalidValueError,
  MissingJsonKeyError,
  SigoptValidationError,
)


def validate(json_dict, schema) -> None:
  try:
    validate_against_schema(json_dict, schema)
  except ValidationError as e:
    raise process_error(e) from e


def is_integer(num):
  if isinstance(num, bool):
    return False
  elif isinstance(num, Integral):
    return True
  else:
    return False


def get_path_string(path):
  strings = (f"[{part}]" if is_integer(part) else f".{part}" for part in path)
  return "".join(strings)


def process_error(e):
  if e.validator == "additionalProperties" and e.validator_value is False:
    unknown_keys = re.findall(r"u?'(\w+)',?", e.message)
    unknown_keys_str = ", ".join([f"`{p}`" for p in unknown_keys])
    msg = f"Unknown json keys {unknown_keys_str} in: {json.dumps(e.instance)}"
    invalid_key = unknown_keys[0] if len(unknown_keys) > 0 else None
    return InvalidKeyError(invalid_key, msg)
  elif e.validator == "type":
    expected_type = str(e.schema["type"])
    return InvalidTypeError(e.instance, expected_type, key=get_path_string(e.path))
  elif e.validator in ["maxProperties", "minProperties"]:
    least_most = "at least" if e.validator == "minProperties" else "at most"
    return SigoptValidationError(f"Expected {least_most} {e.validator_value} keys in {json.dumps(e.instance)}")
  elif e.validator == "required":
    if isinstance(e.instance, Mapping):
      missing_keys = [key for key in e.validator_value if key not in e.instance]
      missing_key = missing_keys[0] if len(missing_keys) > 0 else None
    else:
      missing_key = e.validator_value[0]
    return MissingJsonKeyError(missing_key, e.instance)
  elif e.validator in ["minimum", "maximum"]:
    key = get_path_string(e.path)
    greater_less = "greater than" if e.validator == "minimum" else "less than"
    return InvalidValueError(f"{key} must be {greater_less} or equal to {e.validator_value}")
  elif e.validator in ["minLength", "maxLength", "minItems", "maxItems"]:
    key = get_path_string(e.path)
    greater_less = "greater than" if e.validator in ["minLength", "minItems"] else "less than"
    return InvalidValueError(f"The length of {key} must be {greater_less} or equal to {e.validator_value}")
  elif e.validator == "enum":
    allowed_values = ", ".join([str(s) for s in e.validator_value if s is not None])
    return SigoptValidationError(f"{e.instance} is not one of the allowed values: {allowed_values}")
  elif e.validator == "pattern":
    return SigoptValidationError(f"{e.instance} does not match the regular expression /{e.validator_value}/")
  elif e.validator in ["oneOf", "anyOf"]:
    if len(e.context) > 0:
      return process_error(e.context[0])
    return NotImplementedError("Error has no context but it is oneOf or anyOf")
  else:
    return NotImplementedError(f"Unrecognized error {e.validator} parsing json: {json.dumps(e.instance)}")
