# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.file.model import File, FileData

from integration.service.test_base import ServiceBase


class TestFileServiceFind(ServiceBase):
  @pytest.fixture
  def organization(self, services):
    organization = self.make_organization(services, "Test Organization File Service Count Bytes")
    return organization

  @pytest.fixture
  def client_1(self, services, organization):
    client = self.make_client(services, "Test Client 1 File Service Count Bytes", organization)
    return client

  @pytest.fixture
  def client_2(self, services, organization):
    client = self.make_client(services, "Test Client 2 File Service Count Bytes", organization)
    return client

  @pytest.fixture
  def other_client(self, services):
    organization = self.make_organization(services, "Other Test Organization File Service Count Bytes")
    client = self.make_client(services, "Other Test Client File Service Count Bytes", organization)
    return client

  def insert_file(self, services, client, name, size):
    file_obj = File(client_id=client.id, created_by=None, name=name, data=FileData(content_length=size))
    services.database_service.insert(file_obj)
    return file_obj

  def test_count_bytes_used_by_organization(self, services, organization, client_1, client_2, other_client):
    assert organization.id == client_1.organization_id
    assert organization.id == client_2.organization_id

    byte_count = services.file_service.count_bytes_used_by_organization(organization.id)
    assert byte_count == 0

    self.insert_file(services, client_1, "test bytes used 1 of 4", 1)
    byte_count = services.file_service.count_bytes_used_by_organization(organization.id)
    assert byte_count == 1

    self.insert_file(services, client_2, "test bytes used 2 of 4", 2)
    byte_count = services.file_service.count_bytes_used_by_organization(organization.id)
    assert byte_count == 3

    self.insert_file(services, other_client, "test bytes used 3 of 4", 4)
    byte_count = services.file_service.count_bytes_used_by_organization(organization.id)
    assert byte_count == 3

    self.insert_file(services, client_1, "test bytes used 4 of 4", 8)
    byte_count = services.file_service.count_bytes_used_by_organization(organization.id)
    assert byte_count == 11
