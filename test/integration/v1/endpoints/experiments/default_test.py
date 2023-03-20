# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from integration.v1.constants import DEFAULT_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase


class TestDefaultExperiments(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self):
    return copy.deepcopy(DEFAULT_EXPERIMENT_META)
