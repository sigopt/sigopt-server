# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import String, cast, func

from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment

from integration.service.db.test_base import DatabaseServiceBase


class TestInsertFrom(DatabaseServiceBase):
  EXPERIMENT_ID_SEQUENCE_NAME = "experiments_id_seq"

  def find_experiment(self, database_service, experiment_id):
    experiment = database_service.one(database_service.query(Experiment).filter(Experiment.id == experiment_id))
    assert experiment.id == experiment_id
    return experiment

  def test_insert_from(self, services):
    database_service = services.database_service
    experiment_id = -database_service.count(database_service.query(Experiment)) - 1
    experiment_name = random_string()
    experiment = Experiment(name=experiment_name)

    inserted = database_service.insert_from(
      experiment,
      insert_dict={
        Experiment.id: -func.count(Experiment.id) - 1,
      },
      returning=Experiment.id,
    )
    assert len(inserted) == 1
    row = inserted[0]
    assert len(row) == 1
    inserted_id = row[0]
    assert inserted_id == experiment_id
    inserted_experiment = self.find_experiment(database_service, inserted_id)
    assert inserted_experiment is not None
    assert inserted_experiment.name == experiment_name

  def test_insert_from_multiple(self, services):
    database_service = services.database_service
    experiment_name = random_string()
    experiments = []
    for _ in range(2):
      experiment = Experiment(name=experiment_name)
      database_service.insert(experiment)
      experiments.append(experiment)

    database_service.reserve_ids(self.EXPERIMENT_ID_SEQUENCE_NAME, len(experiments))

    experiment_template = Experiment()
    inserted = database_service.insert_from(
      experiment_template,
      insert_dict={
        Experiment.id: Experiment.id + len(experiments),
        Experiment.name: Experiment.name + cast(Experiment.id, String),
      },
      returning=Experiment.id,
      where_clause=lambda q: q.where(Experiment.name == experiment_name),
    )
    inserted.sort(key=lambda row: row[0])
    assert len(inserted) == len(experiments)
    for row, experiment in zip(inserted, experiments):
      assert len(row) == 1
      inserted_id = row[0]
      inserted_experiment = self.find_experiment(database_service, inserted_id)
      assert inserted_experiment.name == f"{experiment_name}{experiment.id}"
