# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Literal, Mapping, Optional

from zigopt.common import *
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.file.model import File  # type: ignore
from zigopt.json.builder.json_builder import (
  JsonBuilder,
  JsonBuilderValidationType,
  ValidationType,
  expose_fields,
  field,
)
from zigopt.protobuf.gen.file.filedata_pb2 import FileData  # type: ignore


class FileJsonBuilder(JsonBuilder):
  object_name = "file"

  def __init__(
    self,
    file_obj: File,
    download_info: Optional[JsonBuilder] = None,
    upload_info: Optional[JsonBuilder] = None,
  ):
    super().__init__()
    self._file_obj = file_obj
    self._download_info = download_info
    self._upload_info = upload_info

  @expose_fields(
    fields=[
      ("id", ValidationType.id),
      ("name", ValidationType.string),
      ("filename", ValidationType.string),
    ]
  )
  def file_obj(self) -> File:
    return self._file_obj

  @field(ValidationType.id)
  def client(self) -> int:
    return self._file_obj.client_id

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._file_obj.created_by

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._file_obj.date_created, datetime_to_seconds)

  @expose_fields(
    fields=[
      ("content_length", ValidationType.positive_integer),
      ("content_type", ValidationType.mime_type),
      ("content_md5", ValidationType.md5),
    ]
  )
  def file_data(self) -> FileData:
    return self._file_obj.data

  def hide_download(self):
    return self._download_info is None

  @field(JsonBuilderValidationType(), hide=hide_download)
  def download(self) -> Optional[JsonBuilder]:
    return self._download_info

  def hide_upload(self):
    return self._upload_info is None

  @field(JsonBuilderValidationType(), hide=hide_upload)
  def upload(self) -> Optional[JsonBuilder]:
    return self._upload_info


class S3UploadJsonBuilder(JsonBuilder):
  object_name = "s3_upload"

  def __init__(self, url: str, method: Literal["POST"] | Literal["PUT"], headers: Mapping[str, str]):
    self._url = url
    self._method = method
    self._headers = headers

  @field(ValidationType.string)
  def url(self):
    return self._url

  @field(ValidationType.string)
  def method(self) -> str:
    return self._method

  @field(ValidationType.objectOf(ValidationType.string))
  def headers(self) -> Mapping[str, str]:
    return self._headers


class S3DownloadJsonBuilder(JsonBuilder):
  object_name = "s3_download"

  def __init__(self, url: str):
    self._url = url

  @field(ValidationType.string)
  def url(self) -> str:
    return self._url
