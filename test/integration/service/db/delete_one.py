# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from zigopt.client.model import Client
from zigopt.common.strings import random_string
from zigopt.organization.model import Organization
from zigopt.token.model import Token

from integration.service.db.test_base import DatabaseServiceBase


# pylint: disable=attribute-defined-outside-init


class TestDeleteOne(DatabaseServiceBase):
  @pytest.fixture(autouse=True)
  def _setup(self, services):
    self.organization = Organization(name="test delete_one org")
    services.database_service.insert(self.organization)
    self.client = Client(organization_id=self.organization.id, name="test delete_one client")
    services.database_service.insert(self.client)
    self.t1 = Token(client_id=self.client.id, token=random_string())
    services.database_service.insert(self.t1)
    self.t2 = Token(client_id=self.client.id, token=random_string())
    services.database_service.insert(self.t2)
    self._assert_no_deletes(services)

  def _assert_no_deletes(self, services):
    assert (
      services.database_service.count(services.database_service.query(Token).filter(Token.client_id == self.client.id))
      == 2
    )

  @pytest.mark.parametrize("deleter", ["delete_one", "delete_one_or_none"])
  def test_delete_one(self, services, deleter):
    assert (
      getattr(services.database_service, deleter)(
        services.database_service.query(Token).filter(Token.token == self.t1.token),
      )
      == 1
    )
    assert (
      services.database_service.count(
        services.database_service.query(Token).filter(Token.client_id == self.client.id),
      )
      == 1
    )

  @pytest.mark.parametrize("deleter", ["delete_one", "delete_one_or_none"])
  def test_delete_one_multiple_results(self, services, deleter):
    with pytest.raises(MultipleResultsFound):
      getattr(services.database_service, deleter)(
        services.database_service.query(Token).filter(Token.client_id == self.client.id),
      )
    self._assert_no_deletes(services)

  def test_delete_one_no_result(self, services):
    with pytest.raises(NoResultFound):
      services.database_service.delete_one(
        services.database_service.query(Token).filter(Token.client_id == self.client.id + 1),
      )
    self._assert_no_deletes(services)

  def test_delete_one_or_none_no_result(self, services):
    services.database_service.delete_one_or_none(
      services.database_service.query(Token).filter(Token.client_id == self.client.id + 1),
    )
    self._assert_no_deletes(services)
