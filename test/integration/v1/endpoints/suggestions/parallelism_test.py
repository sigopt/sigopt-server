# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from integration.v1.experiments_test_base import ExperimentsTestBase


class TestParallelism(ExperimentsTestBase):
  @pytest.fixture
  def meta(self, any_meta):
    return copy.deepcopy(any_meta)

  def test_create_more_suggestions_than_bandwidth(self, connection, client_id, meta):
    parallel_bandwidth = 2
    meta.update(parallel_bandwidth=parallel_bandwidth)

    e = connection.clients(client_id).experiments().create(**meta)
    for _ in range(parallel_bandwidth):
      connection.experiments(e.id).suggestions().create()

    # TODO: check for soft exception
    connection.experiments(e.id).suggestions().create()

    assert connection.experiments(e.id).suggestions().fetch(state="open", limit=0).count == parallel_bandwidth + 1
