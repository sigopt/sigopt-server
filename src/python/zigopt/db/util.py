# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from enum import Enum


class DeleteClause(Enum):
  NOT_DELETED = 1
  DELETED = 3
  ALL = 2
