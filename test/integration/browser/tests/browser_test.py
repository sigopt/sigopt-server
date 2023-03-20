# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.web.test_base import WebBase


@pytest.mark.slow
class BrowserTest(WebBase):
  pass
