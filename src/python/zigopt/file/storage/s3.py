# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import uuid

from zigopt.file.storage.base import FileStorage
from zigopt.json.builder import S3DownloadJsonBuilder, S3UploadJsonBuilder
from zigopt.protobuf.gen.file.filedata_pb2 import S3StorageMethod
from zigopt.protobuf.lib import CopyFrom


class S3FileStorage(FileStorage):
  DEFAULT_HTTP_UPLOAD_METHOD = "PUT"

  def check_enabled(self):
    s3_service = self.services.s3_user_upload_service
    if not s3_service.enabled:
      raise Exception("S3 user uploads are not enabled")

  def get_key_from_file(self, file_obj):
    assert file_obj.client_id is not None
    download_filename = file_obj.get_download_filename()
    assert download_filename
    return "/".join(
      [
        str(file_obj.client_id),
        str(uuid.uuid4()),
        download_filename,
      ]
    )

  def set_file_storage_method(self, file_obj):
    if file_obj.data.WhichOneof("storage_method") == "s3":
      return
    CopyFrom(file_obj.data.s3, S3StorageMethod(key=self.get_key_from_file(file_obj)))

  def create_upload_data(self, file_obj):
    self.check_enabled()
    s3_service = self.services.s3_user_upload_service
    method = self.DEFAULT_HTTP_UPLOAD_METHOD
    content_length = file_obj.data.content_length
    content_md5_base64 = file_obj.content_md5_base64
    content_type = file_obj.data.content_type
    url, headers = s3_service.generate_upload_info(
      content_length=content_length,
      content_md5_base64=content_md5_base64,
      content_type=content_type,
      key=file_obj.data.s3.key,
      method=method,
    )
    return S3UploadJsonBuilder(
      url=url,
      method=method,
      headers=headers,
    )

  def create_download_data(self, file_obj):
    self.check_enabled()
    s3_service = self.services.s3_user_upload_service
    url = s3_service.generate_download_info(
      key=file_obj.data.s3.key,
    )
    return S3DownloadJsonBuilder(url=url)
