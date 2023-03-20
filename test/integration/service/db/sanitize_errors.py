# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sqlalchemy.exc import IntegrityError

from zigopt.experiment.model import Experiment

from integration.service.db.test_base import DatabaseServiceBase


class TestSanitizeErrors(DatabaseServiceBase):
  def test_integrity_error(self, database_service):
    with pytest.raises(IntegrityError):
      database_service.insert(Experiment(id=-1))
      database_service.insert(Experiment(id=-1))
