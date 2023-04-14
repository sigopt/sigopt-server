# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from integration.v1.constants import DEFAULT_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestExperimentsRandom(ExperimentsTestBase):
  @pytest.fixture
  def experiment_meta_random(self):
    meta = copy.deepcopy(DEFAULT_EXPERIMENT_META)
    meta["type"] = "random"
    return meta

  def test_create_random(self, connection, client_id, experiment_meta_random):
    e = connection.clients(client_id).experiments().create(**experiment_meta_random)
    assert e.id is not None
