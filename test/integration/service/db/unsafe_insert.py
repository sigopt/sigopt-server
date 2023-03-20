# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment

from integration.service.db.test_base import DatabaseServiceBase


class TestUnsafeInsert(DatabaseServiceBase):
  def test_insert_all(self, database_service):
    experiments = database_service.all(database_service.query(Experiment))
    with pytest.raises(ValueError):
      database_service.insert_all(experiments)

  def test_insert(self, database_service):
    experiment = database_service.first(database_service.query(Experiment))
    with pytest.raises(ValueError):
      database_service.insert(experiment)
