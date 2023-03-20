# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.experiment.model import Experiment

from integration.service.db.test_base import DatabaseServiceBase


class TestUpsert(DatabaseServiceBase):
  NEW_NAME = "name_2"
  EXPERIMENT_ID_SEQUENCE_NAME = "experiments_id_seq"

  def test_upsert_as_insert(self, services):
    experiment_id = services.database_service.reserve_ids(self.EXPERIMENT_ID_SEQUENCE_NAME, 1)[0]
    experiment = Experiment(id=experiment_id, name=self.INITIAL_EXPERIMENT_NAME)

    services.database_service.upsert(experiment)
    inserted_experiment = services.experiment_service.find_by_id(experiment_id)
    assert inserted_experiment is not None
    assert inserted_experiment.name == self.INITIAL_EXPERIMENT_NAME

  def test_upsert_as_update(self, services, experiment):
    updated_experiment = Experiment(
      id=experiment.id,
      name=self.NEW_NAME,
    )
    services.database_service.upsert(updated_experiment)
    inserted_experiment = services.experiment_service.find_by_id(experiment.id)
    assert inserted_experiment is not None
    assert inserted_experiment.name == self.NEW_NAME

  def test_upsert_with_skip_none(self, services, experiment):
    updated_experiment = Experiment(id=experiment.id, name=None)
    services.database_service.upsert(updated_experiment, skip_none=True)
    inserted_experiment = services.experiment_service.find_by_id(experiment.id)
    assert inserted_experiment is not None
    assert inserted_experiment.name == self.INITIAL_EXPERIMENT_NAME

  def test_upsert_as_insert_with_skip_none(self, services):
    experiment_id = services.database_service.reserve_ids(self.EXPERIMENT_ID_SEQUENCE_NAME, 1)[0]
    experiment = Experiment(id=experiment_id)

    services.database_service.upsert(experiment, skip_none=True)
    inserted_experiment = services.experiment_service.find_by_id(experiment_id)
    # Assert that the fields have the expected default values
    assert inserted_experiment is not None
    assert inserted_experiment.name is None
    assert is_boolean(inserted_experiment.deleted)

  def upsert_where_client(self, services, experiment, client_id):
    updated_experiment = Experiment(
      id=experiment.id,
      name=self.NEW_NAME,
    )
    where = Experiment.client_id == client_id
    services.database_service.upsert(updated_experiment, where)
    return experiment.id

  def test_upsert_as_update_where_successful(self, services, experiment, client):
    experiment_id = self.upsert_where_client(services, experiment, client.id)
    inserted_experiment = services.experiment_service.find_by_id(experiment_id)
    assert inserted_experiment is not None
    assert inserted_experiment.name == self.NEW_NAME

  def test_upsert_as_update_where_unsuccessful(self, services, experiment, client):
    experiment_id = self.upsert_where_client(services, experiment, client.id + 1)
    inserted_experiment = services.experiment_service.find_by_id(experiment_id)
    assert inserted_experiment is not None
    assert inserted_experiment.name != self.NEW_NAME
