# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.handlers.validate.base import validate_name
from zigopt.organization.model import Organization

from libsigopt.aux.errors import SigoptValidationError


def validate_organization_name(name: Optional[str]) -> str:
  name = validate_name(name)
  if len(name) >= Organization.NAME_MAX_LENGTH:
    raise SigoptValidationError(f"Name must be fewer than {Organization.NAME_MAX_LENGTH} characters")
  return name
