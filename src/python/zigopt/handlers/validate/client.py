# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.client.model import Client
from zigopt.handlers.validate.base import validate_name

from libsigopt.aux.errors import SigoptValidationError


def validate_client_name(name: str) -> str:
  name = validate_name(name)
  if len(name) >= Client.NAME_MAX_LENGTH:
    raise SigoptValidationError(f"Name must be fewer than {Client.NAME_MAX_LENGTH} characters")
  return name
