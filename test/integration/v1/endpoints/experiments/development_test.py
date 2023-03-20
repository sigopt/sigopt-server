# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestDevelopmentExperiments(ExperimentsTestBase):
  def test_create_development_experiment(self, development_connection):
    e = development_connection.create_any_experiment()
    # TODO(SN-1138): update public clients
    assert e.development is True
    e = development_connection.experiments(e.id).fetch()
    assert e.development is True
    s = development_connection.experiments(e.id).suggestions().create()
    development_connection.experiments(e.id).observations().create(
      values=[{"value": 1.0}],
      suggestion=s.id,
    )
    development_connection.experiments(e.id).delete()
