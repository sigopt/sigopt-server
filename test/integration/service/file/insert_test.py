# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.file.model import File, FileData

from integration.service.test_base import ServiceBase


class TestFileServiceInsert(ServiceBase):
  @pytest.fixture
  def client(self, services):
    organization = self.make_organization(services, "Test Organization File Insert")
    client = self.make_client(services, "Test Client File Insert", organization)
    return client

  def test_insert_file(self, services, client):
    file_obj = File(
      client_id=client.id,
      created_by=None,
      name="test insert",
      filename="xyz.txt",
      data=FileData(content_type="text/plain", content_md5=b"\0" * 16, content_length=1),
    )
    assert file_obj.data.WhichOneof("storage_method") is None
    services.file_service.insert_file_and_create_upload_data(file_obj)
    assert file_obj.data.WhichOneof("storage_method") == "s3"
    assert file_obj.data.s3.key is not None
    assert file_obj.data.s3.key.endswith("/xyz.txt")
