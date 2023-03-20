# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from zigopt.client.model import Client
from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment
from zigopt.organization.model import Organization

from integration.service.db.test_base import DatabaseServiceBase


# pylint: disable=attribute-defined-outside-init

UPDATE_CLAUSE = {
  Experiment.client_id: None,
  Experiment.name: random_string(),
}


class TestUpdateOne(DatabaseServiceBase):
  @pytest.fixture(autouse=True)
  def _setup(self, services):
    self.organization = Organization(name="test update_one org")
    services.database_service.insert(self.organization)
    self.client = Client(organization_id=self.organization.id, name="test update_one client")
    services.database_service.insert(self.client)
    self.e1 = Experiment(client_id=self.client.id, name="test_update_one experiment 1")
    services.database_service.insert(self.e1)
    self.e2 = Experiment(client_id=self.client.id, name="test_update_one experiment 2")
    services.database_service.insert(self.e2)
    self._assert_no_updates(services)

  def _assert_no_updates(self, services):
    q = services.database_service.query(Experiment)
    for k, v in UPDATE_CLAUSE.items():
      q = q.filter(k == v)
    assert services.database_service.count(q) == 0

  @pytest.mark.parametrize("updater", ["update_one", "update_one_or_none"])
  def test_update_one(self, services, updater):
    new_name = random_string()
    assert (
      getattr(services.database_service, updater)(
        services.database_service.query(Experiment).filter(Experiment.id == self.e1.id),
        {Experiment.name: new_name},
      )
      == 1
    )
    assert (
      services.database_service.count(
        services.database_service.query(Experiment).filter(Experiment.name == new_name),
      )
      == 1
    )

  @pytest.mark.parametrize("updater", ["update_one", "update_one_or_none"])
  def test_update_one_multiple_results(self, services, updater):
    with pytest.raises(MultipleResultsFound):
      getattr(services.database_service, updater)(
        services.database_service.query(Experiment).filter(Experiment.client_id == self.client.id),
        UPDATE_CLAUSE,
      )
    self._assert_no_updates(services)

  def test_update_one_no_result(self, services):
    with pytest.raises(NoResultFound):
      services.database_service.update_one(
        services.database_service.query(Experiment).filter(Experiment.client_id == self.client.id + 1),
        UPDATE_CLAUSE,
      )
    self._assert_no_updates(services)

  def test_update_one_or_none_no_result(self, services):
    services.database_service.update_one_or_none(
      services.database_service.query(Experiment).filter(Experiment.client_id == self.client.id + 1),
      UPDATE_CLAUSE,
    )
    self._assert_no_updates(services)
