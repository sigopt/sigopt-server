# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigopt import Connection

from sigoptlite.driver import LocalDriver
from sigoptlitetest.base_test import UnitTestsBase


class UnitTestsEndpoint(UnitTestsBase):
  conn = Connection(driver=LocalDriver)
