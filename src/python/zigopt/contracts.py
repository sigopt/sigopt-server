# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

import deal


def prepare_contracts():
  if os.environ.get("ENABLE_CONTRACTS"):
    deal.enable()
  else:
    deal.disable(permament=True)  # typo is intentional, this is how deal defines the argument
