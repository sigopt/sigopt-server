# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, func

from zigopt.client.model import Client
from zigopt.file.model import File
from zigopt.file.storage.s3 import S3FileStorage
from zigopt.services.base import Service


class FileService(Service):
  def __init__(self, services):
    super().__init__(services)

  @property
  def enabled(self):
    return self.services.config_broker.get("user_uploads.s3.enabled", False)

  def find_by_id(self, file_id):
    return self.services.database_service.one_or_none(
      self.services.database_service.query(File).filter(File.id == file_id)
    )

  def get_file_storage(self, file_obj):
    storage_class = S3FileStorage
    return storage_class(self.services)

  def create_download_data(self, file_obj):
    file_storage = self.get_file_storage(file_obj)
    return file_storage.create_download_data(file_obj)

  def insert_file_and_create_upload_data(self, file_obj):
    file_storage = self.get_file_storage(file_obj)
    file_storage.set_file_storage_method(file_obj)
    upload_data = file_storage.create_upload_data(file_obj)
    self.services.database_service.insert(file_obj)
    return file_obj, upload_data

  def count_bytes_used_by_organization(self, organization_id):
    return self.services.database_service.scalar(
      self.services.database_service.query(
        func.coalesce(
          func.sum(
            func.coalesce(
              File.data.content_length.real_astext.cast(BigInteger),
              0,
            )
          ),
          0,
        )
      )
      .join(Client, Client.id == File.client_id)
      .filter(Client.organization_id == organization_id)
    )
