# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.test_base import ServiceBase


def get_id(obj):
  return obj.id


class TestClientServiceFind(ServiceBase):
  organization_a = organization_b = None
  client_a = client_b = client_c = None

  @pytest.fixture(autouse=True)
  def setup(self, services):
    if any(
      item is None
      for item in (
        self.organization_a,
        self.organization_b,
        self.client_a,
        self.client_b,
        self.client_c,
      )
    ):
      self.organization_a, self.organization_b = (
        self.make_organization(services, f"Test Organization {i}") for i in (1, 2)
      )
      self.client_a, self.client_b = (
        self.make_client(services, f"Test Client {i}", self.organization_a) for i in (1, 2)
      )
      self.client_c = self.make_client(services, "Test Client 3", self.organization_b)

  def test_find_by_ids_or_organization_ids_empty_args(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[],
      organization_ids=[],
    )
    assert clients == []

  def test_find_by_ids_or_organization_ids_empty_organizations(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[self.client_a.id, self.client_c.id],
      organization_ids=[],
    )
    assert clients is not None
    assert len(clients) == 2
    assert set(get_id(c) for c in clients) == set((self.client_a.id, self.client_c.id))

  def test_find_by_ids_or_organization_ids_empty_clients(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[],
      organization_ids=[self.organization_a.id, self.organization_b.id],
    )
    assert clients is not None
    assert len(clients) == 3
    assert set(get_id(c) for c in clients) == set((self.client_a.id, self.client_b.id, self.client_c.id))

  def test_find_by_ids_or_organization_ids_clients_xor_organizations(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[self.client_a.id, self.client_b.id],
      organization_ids=[self.organization_b.id],
    )
    assert clients is not None
    assert len(clients) == 3
    assert set(get_id(c) for c in clients) == set((self.client_a.id, self.client_b.id, self.client_c.id))

  def test_find_by_ids_or_organization_ids_clients_and_organizations(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[self.client_a.id, self.client_b.id],
      organization_ids=[self.organization_a.id],
    )
    assert clients is not None
    assert len(clients) == 2
    assert set(get_id(c) for c in clients) == set((self.client_a.id, self.client_b.id))

  def test_find_by_ids_or_organization_ids_all(self, services):
    clients = services.client_service.find_by_ids_or_organization_ids(
      client_ids=[self.client_a.id, self.client_b.id, self.client_c.id],
      organization_ids=[self.organization_a.id, self.organization_b.id],
    )
    assert clients is not None
    assert len(clients) == 3
    assert set(get_id(c) for c in clients) == set((self.client_a.id, self.client_b.id, self.client_c.id))
