# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.client.model import Client  # type: ignore
from zigopt.handlers.validate.base import validate_name
from zigopt.net.errors import BadParamError  # type: ignore


def validate_client_name(name: str) -> str:
  name = validate_name(name)
  if len(name) >= Client.NAME_MAX_LENGTH:
    raise BadParamError(f"Name must be fewer than {Client.NAME_MAX_LENGTH} characters")
  return name
