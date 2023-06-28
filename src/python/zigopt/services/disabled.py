# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.services.base import BaseService


class DisabledService(BaseService):
  @property
  def enabled(self):
    return False

  def warmup(self):
    pass
