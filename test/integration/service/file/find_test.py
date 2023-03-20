# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.file.model import File, FileData

from integration.service.test_base import ServiceBase


class TestFileServiceFind(ServiceBase):
  @pytest.fixture
  def client(self, services):
    organization = self.make_organization(services, "Test Organization File Service Find")
    client = self.make_client(services, "Test Client File Service Find", organization)
    return client

  def insert_file(self, services, client, name):
    file_obj = File(client_id=client.id, created_by=None, name=name, data=FileData())
    services.database_service.insert(file_obj)
    return file_obj

  @pytest.fixture
  def file_1(self, services, client):
    return self.insert_file(services, client, "test find 1")

  @pytest.fixture
  def file_2(self, services, client):
    return self.insert_file(services, client, "test find 2")

  def test_find_by_id(self, services, file_1, file_2):
    assert file_1.id != file_2.id
    found = services.file_service.find_by_id(-1000)
    assert found is None

    found = services.file_service.find_by_id(file_1.id)
    assert found is not None
    assert found.id == file_1.id

    found = services.file_service.find_by_id(file_2.id)
    assert found is not None
    assert found.id == file_2.id
