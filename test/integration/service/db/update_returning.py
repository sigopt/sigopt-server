# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import and_

from zigopt.experiment.model import Experiment

from integration.service.db.test_base import DatabaseServiceBase


class TestUpdateReturning(DatabaseServiceBase):
  NEW_NAME = "new experiment name"
  NEW_VALUES = {Experiment.name.name: NEW_NAME}

  def test_update_returning(self, services, experiment):
    assert experiment.name != self.NEW_NAME

    rows = list(
      services.database_service.update_returning(
        Experiment, where=(Experiment.id == experiment.id), values=self.NEW_VALUES
      )
    )
    assert len(rows) == 1
    for row in rows:
      assert row.name == self.NEW_NAME

    # show that we persisted the update for the experiment (commited the change)
    db_experiment = services.experiment_service.find_by_id(experiment.id)
    assert db_experiment.name == self.NEW_NAME

  def test_update_returning_where_unsuccessful(self, services, experiment, client):
    assert experiment.name != self.NEW_NAME

    rows = list(
      services.database_service.update_returning(
        Experiment,
        where=and_(Experiment.id == experiment.id, Experiment.client_id == client.id + 1),
        values=self.NEW_VALUES,
      )
    )
    assert len(rows) == 0
    db_experiment = services.experiment_service.find_by_id(experiment.id)
    assert db_experiment.name != self.NEW_NAME
