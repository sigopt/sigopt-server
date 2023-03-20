# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestDeleteExperiments(ExperimentsTestBase, TrainingRunTestMixin):
  def test_experiment_delete(self, connection, any_meta):
    e = connection.clients(connection.client_id).experiments().create(**any_meta)
    assert connection.experiments(e.id).fetch().state != "deleted"
    connection.experiments(e.id).delete()
    assert connection.experiments(e.id).fetch().state == "deleted"

    connection.experiments(e.id).update(state="active")
    assert connection.experiments(e.id).fetch().state != "deleted"
    connection.experiments(e.id).delete()

    # Should be idempotent
    connection.experiments(e.id).delete()
    assert connection.experiments(e.id).fetch().state == "deleted"
