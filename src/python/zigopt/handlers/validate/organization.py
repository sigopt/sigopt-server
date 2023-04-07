# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.handlers.validate.base import validate_name
from zigopt.net.errors import BadParamError
from zigopt.organization.model import Organization


def validate_organization_name(name: Optional[str]) -> str:
  name = validate_name(name)
  if len(name) >= Organization.NAME_MAX_LENGTH:
    raise BadParamError("Name must be fewer than %s characters" % Organization.NAME_MAX_LENGTH)
  return name
